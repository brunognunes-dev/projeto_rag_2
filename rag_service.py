import httpx
from config import config
from embedding_service import embedding_service
from database import db_manager

NO_DATA_RESPONSE = "Sem dados disponíveis na base"

class RAGService:
    def __init__(self):
        self.similarity_threshold = 0.25

    def query(self, user_question: str) -> dict:
        if not user_question or not user_question.strip():
            return {
                "success": False,
                "error": "Pergunta vazia",
                "final_response": NO_DATA_RESPONSE
            }

        # Step 1: PERGUNTA
        pipeline_steps = []
        pipeline_steps.append({
            "step": "PERGUNTA",
            "status": "Concluído",
            "detail": f"Pergunta recebida: '{user_question}'"
        })

        # Step 2: TOKENIZAÇÃO
        q_tokens = len(user_question.split())
        pipeline_steps.append({
            "step": "TOKENIZAÇÃO",
            "status": "Concluído",
            "detail": f"Pergunta tokenizada (aprox. {q_tokens} tokens)"
        })

        # Step 3: EMBEDDING (FastEmbed)
        pipeline_steps.append({
            "step": "EMBEDDING",
            "status": "Em andamento",
            "detail": "Gerando embedding da pergunta via FastEmbed..."
        })
        q_embedding = embedding_service.generate_embedding(user_question)
        pipeline_steps[2]["status"] = "Concluído"
        pipeline_steps[2]["detail"] = f"Vetor vetorial de dimensão {len(q_embedding)} gerado com sucesso."

        # Step 4: RETRIEVAL (Top 5 Cosine Similarity)
        pipeline_steps.append({
            "step": "RETRIEVAL",
            "status": "Em andamento",
            "detail": "Consultando base PGVECTOR (Top 5 candidatos)..."
        })

        candidates = db_manager.search_similar(q_embedding, top_k=5)
        
        # Filter candidates by similarity threshold
        relevant_candidates = [c for c in candidates if c["score"] >= self.similarity_threshold]

        pipeline_steps[3]["status"] = "Concluído"
        pipeline_steps[3]["detail"] = f"{len(candidates)} candidatos encontrados ({len(relevant_candidates)} acima do limiar de relevância {self.similarity_threshold})."

        # SECTION 15 RULE: If no relevant candidates exist or base is empty
        if not candidates or not relevant_candidates:
            pipeline_steps.append({
                "step": "PROMPT AUMENTADO",
                "status": "Ignorado",
                "detail": "Sem contexto relevante. LLM não será acionado."
            })
            pipeline_steps.append({
                "step": "LLM",
                "status": "Finalizado",
                "detail": "Resposta direta por ausência de dados."
            })

            return {
                "success": True,
                "pipeline_steps": pipeline_steps,
                "candidates": candidates,
                "relevant_candidates": [],
                "augmented_prompt": "Nenhum contexto construído.",
                "final_response": NO_DATA_RESPONSE
            }

        # Step 5: PROMPT AUMENTADO
        context_parts = []
        for idx, cand in enumerate(relevant_candidates, start=1):
            context_parts.append(
                f"[Documento {idx}]: {cand['document_name']} (Score: {cand['score']})\n"
                f"Conteúdo: {cand['content']}\n"
            )
        
        context_str = "\n".join(context_parts)
        
        augmented_prompt = (
            "Você é um assistente especializado de RAG didático. "
            "Responda à pergunta do usuário EXCLUSIVAMENTE utilizando as informações do contexto abaixo. "
            "Se a resposta não puder ser extraída diretamente do contexto, responda EXATAMENTE: 'Sem dados disponíveis na base'.\n\n"
            f"--- CONTEXTO RECUPERADO ---\n{context_str}\n"
            "---------------------------\n\n"
            f"PERGUNTA: {user_question}\n"
            "RESPOSTA:"
        )

        pipeline_steps.append({
            "step": "PROMPT AUMENTADO",
            "status": "Concluído",
            "detail": f"Prompt construído com {len(relevant_candidates)} fonte(s) de contexto."
        })

        # Step 6: OPENROUTER LLM INTEGRATION
        pipeline_steps.append({
            "step": "LLM",
            "status": "Em andamento",
            "detail": f"Enviando solicitação para OpenRouter ({config.OPENROUTER_MODEL})..."
        })

        llm_response_text = self._call_openrouter(augmented_prompt)

        pipeline_steps[5]["status"] = "Concluído"
        pipeline_steps[5]["detail"] = "Resposta gerada com sucesso pelo LLM."

        return {
            "success": True,
            "pipeline_steps": pipeline_steps,
            "candidates": candidates,
            "relevant_candidates": relevant_candidates,
            "augmented_prompt": augmented_prompt,
            "final_response": llm_response_text
        }

    def _call_openrouter(self, prompt: str) -> str:
        if not config.OPENROUTER_API_KEY:
            return "Erro: OPENROUTER_API_KEY não configurada no .env"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "Você responde perguntas estritamente com base no contexto fornecido."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    res_json = resp.json()
                    choices = res_json.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                    return NO_DATA_RESPONSE
                else:
                    return f"Erro na API OpenRouter (Status {resp.status_code})"
        except Exception as e:
            return f"Erro de comunicação com OpenRouter: {str(e)[:100]}"

rag_service = RAGService()
