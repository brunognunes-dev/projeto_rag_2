import os
from pathlib import Path

from src.services.ocr_ingestion import OCRAndIngestionService


def test_ingestion_uses_raw_dir_and_moves_file_to_gold(tmp_path):
    raw_dir = tmp_path / "documents" / "raw"
    gold_dir = tmp_path / "documents" / "gold"
    raw_dir.mkdir(parents=True)
    gold_dir.mkdir(parents=True)

    pdf_path = raw_dir / "invoice.pdf"
    pdf_path.write_bytes(b"fake pdf content")

    service = OCRAndIngestionService(doc_dir=str(raw_dir), archive_dir=str(gold_dir))

    assert service.list_available_documents() == ["invoice.pdf"]

    moved = service._move_processed_file(pdf_path)

    assert moved is True
    assert not pdf_path.exists()
    assert (gold_dir / "invoice.pdf").exists()
