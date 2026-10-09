import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("[Pipeline Test] 1. Checking backend status...")
    resp = requests.get(f"{BASE_URL}/api/status")
    print("Status response:", resp.json())
    assert resp.status_code == 200

    print("\n[Pipeline Test] 2. Checking available documents...")
    resp = requests.get(f"{BASE_URL}/api/documents")
    docs = resp.json().get("documents", [])
    print("Documents:", docs)
    assert len(docs) == 4

    print("\n[Pipeline Test] 3. Testing Ingestion Pipeline (OCR -> Structured -> FastEmbed -> Vector DB)...")
    resp = requests.post(f"{BASE_URL}/api/ingest", json={"files": docs})
    ing_res = resp.json()
    print("Ingestion result success:", ing_res.get("success"))
    print("Total chunks:", ing_res.get("total_chunks"))
    print("Vector dimension:", ing_res.get("vector_dimension"))
    assert ing_res.get("success") is True

    print("\n[Pipeline Test] 4. Testing RAG Query 1 (Valid Invoice Query)...")
    q1 = "Qual é o valor total da nota fiscal da TechSupply Brasil Ltda emitida para Bruno Gabriel Nunes?"
    resp = requests.post(f"{BASE_URL}/api/query", json={"question": q1})
    q1_res = resp.json()
    print("Query 1 Candidates Top 5:")
    for c in q1_res.get("candidates", []):
        print(f"  - [{c['document_name']}] Score: {c['score']}")
    print("Query 1 LLM Final Response:\n", q1_res.get("final_response"))

    print("\n[Pipeline Test] 5. Testing RAG Query 2 (No Data / Out of Scope Query)...")
    q2 = "Quem ganhou a copa do mundo de futebol de 1970?"
    resp = requests.post(f"{BASE_URL}/api/query", json={"question": q2})
    q2_res = resp.json()
    print("Query 2 Response:", q2_res.get("final_response"))
    assert q2_res.get("final_response") == "Sem dados disponíveis na base"

    print("\n[SUCCESS] ALL END-TO-END RAG PIPELINE TESTS PASSED CLEANLY!")

if __name__ == "__main__":
    time.sleep(2)
    run_tests()
