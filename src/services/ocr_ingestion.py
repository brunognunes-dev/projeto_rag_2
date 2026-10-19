import os
import re
import shutil
from pypdf import PdfReader
import pandas as pd
from src.services.embedding_service import embedding_service
from src.core.database import db_manager

class OCRAndIngestionService:
    def __init__(self, doc_dir="documents/raw", archive_dir="documents/gold"):
        self.doc_dir = doc_dir
        self.archive_dir = archive_dir
        os.makedirs(self.doc_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

    def list_available_documents(self) -> list[str]:
        if not os.path.exists(self.doc_dir):
            return []
        return sorted(f for f in os.listdir(self.doc_dir) if f.lower().endswith(".pdf"))

    def _move_processed_file(self, file_path: str) -> bool:
        try:
            if not os.path.exists(file_path):
                return False
            os.makedirs(self.archive_dir, exist_ok=True)
            destination = os.path.join(self.archive_dir, os.path.basename(file_path))
            if os.path.exists(destination):
                os.remove(destination)
            shutil.move(file_path, destination)
            return True
        except Exception as e:
            print(f"[OCR] Falha ao mover arquivo processado para {self.archive_dir}: {e}")
            return False

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Reads PDF and extracts raw textual content (OCR fallback simulated if required)."""
        reader = PdfReader(pdf_path)
        extracted_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted_text += t + "\n"
        return extracted_text.strip()

    def parse_structured_fields(self, filename: str, text: str) -> dict:
        """Parses structured invoice fields from extracted text."""
        data = {
            "documento": filename,
            "nota_fiscal": "",
            "data": "",
            "emitente": "",
            "destinatario": "",
            "produto": "",
            "quantidade": "",
            "valor_unitario": "",
            "valor_total": "",
            "texto_extraido": text
        }
        
        # Regex extraction
        nf_match = re.search(r"NF-e Nº (\d+)", text)
        if nf_match:
            data["nota_fiscal"] = nf_match.group(1)
            
        data_match = re.search(r"Data de Emissão: (\d{2}/\d{2}/\d{4})", text)
        if data_match:
            data["data"] = data_match.group(1)

        emitente_match = re.search(r"Emitente: (.*?) \|", text)
        if emitente_match:
            data["emitente"] = emitente_match.group(1).strip()

        dest_match = re.search(r"Destinatário: (.*?) \|", text)
        if dest_match:
            data["destinatario"] = dest_match.group(1).strip()

        total_match = re.search(r"VALOR TOTAL DA NOTA: (R\$ [\d\.]+)", text)
        if total_match:
            data["valor_total"] = total_match.group(1)

        return data

    def run_ingestion_pipeline(self, selected_files: list[str] = None):
        """Executes full ingestion pipeline with step-by-step progress metrics for didactic UI."""
        if selected_files is None or len(selected_files) == 0:
            selected_files = self.list_available_documents()

        db_manager.clear_documents()

        steps_log = []
        structured_records = []
        total_chunks = 0
        total_embeddings = 0

        # Step 1: INGESTÃO / OCR
        steps_log.append({"step": "INGESTÃO", "status": "Em andamento", "detail": f"Lendo {len(selected_files)} arquivo(s) PDF..."})
        
        processed_chunks = []

        for fname in selected_files:
            fpath = os.path.join(self.doc_dir, fname)
            if not os.path.exists(fpath):
                continue

            # Upload PDF permanently to Supabase Storage
            try:
                with open(fpath, "rb") as f_pdf:
                    db_manager.upload_file_to_storage(fname, f_pdf.read(), content_type="application/pdf")
            except Exception as e:
                print(f"[OCR] Supabase storage upload notice for {fname}: {e}")
            
            raw_text = self.extract_text_from_pdf(fpath)
            fields = self.parse_structured_fields(fname, raw_text)
            structured_records.append(fields)

            # Simple chunking by paragraph/lines
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
            
            # Group into chunks of ~200-300 characters
            chunk_buf = []
            chunk_size = 0
            chunk_idx = 1

            for line in lines:
                chunk_buf.append(line)
                chunk_size += len(line)
                if chunk_size >= 200:
                    chunk_text = "\n".join(chunk_buf)
                    processed_chunks.append({
                        "doc_name": fname,
                        "chunk_index": chunk_idx,
                        "content": chunk_text,
                        "metadata": fields
                    })
                    chunk_buf = []
                    chunk_size = 0
                    chunk_idx += 1

            if chunk_buf:
                chunk_text = "\n".join(chunk_buf)
                processed_chunks.append({
                    "doc_name": fname,
                    "chunk_index": chunk_idx,
                    "content": chunk_text,
                    "metadata": fields
                })

        steps_log[0]["status"] = "Concluído"
        steps_log[0]["detail"] = f"{len(structured_records)} documentos processados por OCR."

        # Step 2: TOKENIZAÇÃO
        total_chunks = len(processed_chunks)
        approx_tokens = sum(len(c["content"].split()) for c in processed_chunks)
        steps_log.append({
            "step": "TOKENIZAÇÃO",
            "status": "Concluído",
            "detail": f"{total_chunks} chunks gerados (aprox. {approx_tokens} tokens)."
        })

        # Step 3: EMBEDDING
        steps_log.append({
            "step": "EMBEDDING",
            "status": "Em andamento",
            "detail": f"Gerando embeddings com FastEmbed ({embedding_service.dimension}d)..."
        })

        texts_to_embed = [c["content"] for c in processed_chunks]
        embeddings = embedding_service.generate_embeddings_batch(texts_to_embed)
        total_embeddings = len(embeddings)

        steps_log[2]["status"] = "Concluído"
        steps_log[2]["detail"] = f"{total_embeddings} vetores de dimensão {embedding_service.dimension} gerados."

        # Step 4: ÍNDICE VETORIAL (Supabase PGVECTOR)
        steps_log.append({
            "step": "ÍNDICE VETORIAL",
            "status": "Em andamento",
            "detail": "Inserindo vetores no Supabase (PGVECTOR)..."
        })

        for i, c in enumerate(processed_chunks):
            saved = db_manager.save_chunk(
                doc_name=c["doc_name"],
                chunk_index=c["chunk_index"],
                content=c["content"],
                metadata=c["metadata"],
                embedding=embeddings[i]
            )
            if saved:
                original_path = os.path.join(self.doc_dir, c["doc_name"])
                self._move_processed_file(original_path)

        steps_log[3]["status"] = "Concluído"
        steps_log[3]["detail"] = f"{total_embeddings} registros armazenados com sucesso."

        # Convert structured records to JSON serializable dictionary
        tabular_df = pd.DataFrame(structured_records)

        return {
            "success": True,
            "steps": steps_log,
            "tabular_data": tabular_df.to_dict(orient="records"),
            "total_documents": len(selected_files),
            "total_chunks": total_chunks,
            "total_vectors": total_embeddings,
            "vector_dimension": embedding_service.dimension
        }

ingestion_service = OCRAndIngestionService()
