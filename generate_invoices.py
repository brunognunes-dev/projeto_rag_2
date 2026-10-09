import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

os.makedirs("documents", exist_ok=True)

invoices = [
    {
        "filename": "documents/NF_001.pdf",
        "title": "NOTA FISCAL ELETRÔNICA - NF-e Nº 001",
        "data": "15/01/2026",
        "emitente": "TechSupply Brasil Ltda",
        "cnpj_emitente": "12.345.678/0001-90",
        "destinatario": "Bruno Gabriel Nunes",
        "cpf_destinatario": "111.222.333-44",
        "items": [
            {"desc": "Teclado Mecânico RGB Switch Blue", "qtd": 2, "unit": 250.00, "total": 500.00},
            {"desc": "Mouse Gamer Wireless 16000 DPI", "qtd": 1, "unit": 350.00, "total": 350.00}
        ],
        "impostos": "ICMS: R$ 153.00 (18%)",
        "valor_total": "R$ 850.00"
    },
    {
        "filename": "documents/NF_002.pdf",
        "title": "NOTA FISCAL ELETRÔNICA - NF-e Nº 002",
        "data": "02/02/2026",
        "emitente": "DataServer Soluções S.A.",
        "cnpj_emitente": "98.765.432/0001-10",
        "destinatario": "Bruno Gabriel Nunes",
        "cpf_destinatario": "111.222.333-44",
        "items": [
            {"desc": "Servidor Rack 1U Xeon 16-Core", "qtd": 1, "unit": 12000.00, "total": 12000.00},
            {"desc": "Memória RAM 64GB DDR5 ECC", "qtd": 4, "unit": 1500.00, "total": 6000.00}
        ],
        "impostos": "ICMS: R$ 3240.00 (18%)",
        "valor_total": "R$ 18000.00"
    },
    {
        "filename": "documents/NF_003.pdf",
        "title": "NOTA FISCAL ELETRÔNICA - NF-e Nº 003",
        "data": "20/02/2026",
        "emitente": "Oficina Cloud & AI Eireli",
        "cnpj_emitente": "45.678.912/0001-33",
        "destinatario": "Bruno Gabriel Nunes",
        "cpf_destinatario": "111.222.333-44",
        "items": [
            {"desc": "Licença Software RAG Enterprise v2", "qtd": 1, "unit": 4500.00, "total": 4500.00},
            {"desc": "Treinamento Especializado LLM & Python (horas)", "qtd": 10, "unit": 350.00, "total": 3500.00}
        ],
        "impostos": "ISS: R$ 400.00 (5%)",
        "valor_total": "R$ 8000.00"
    },
    {
        "filename": "documents/NF_004.pdf",
        "title": "NOTA FISCAL ELETRÔNICA - NF-e Nº 004",
        "data": "05/03/2026",
        "emitente": "MegaOffice Materiais de Escritório",
        "cnpj_emitente": "33.222.111/0001-55",
        "destinatario": "Bruno Gabriel Nunes",
        "cpf_destinatario": "111.222.333-44",
        "items": [
            {"desc": "Cadeira Ergonômica Premium Mesh", "qtd": 1, "unit": 1800.00, "total": 1800.00},
            {"desc": "Mesa Eletrônica Regulável em Altura", "qtd": 1, "unit": 2700.00, "total": 2700.00}
        ],
        "impostos": "ICMS: R$ 810.00 (18%)",
        "valor_total": "R$ 4500.00"
    }
]

def create_pdf(inv):
    c = canvas.Canvas(inv["filename"], pagesize=letter)
    width, height = letter
    
    # Title & Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, inv["title"])
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"Data de Emissão: {inv['data']}")
    c.drawString(50, height - 95, f"Emitente: {inv['emitente']} | CNPJ: {inv['cnpj_emitente']}")
    c.drawString(50, height - 110, f"Destinatário: {inv['destinatario']} | CPF: {inv['cpf_destinatario']}")
    
    c.line(50, height - 120, width - 50, height - 120)
    
    # Table Header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 140, "Descrição do Produto / Serviço")
    c.drawString(320, height - 140, "Qtd")
    c.drawString(380, height - 140, "Val. Unitario")
    c.drawString(480, height - 140, "Val. Total")
    c.line(50, height - 145, width - 50, height - 145)
    
    y = height - 165
    c.setFont("Helvetica", 10)
    for item in inv["items"]:
        c.drawString(50, y, item["desc"])
        c.drawString(320, y, str(item["qtd"]))
        c.drawString(380, y, f"R$ {item['unit']:.2f}")
        c.drawString(480, y, f"R$ {item['total']:.2f}")
        y -= 20
        
    c.line(50, y, width - 50, y)
    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, f"Impostos: {inv['impostos']}")
    c.drawString(380, y, f"VALOR TOTAL DA NOTA: {inv['valor_total']}")
    
    c.save()
    print(f"Generated {inv['filename']}")

if __name__ == "__main__":
    for inv in invoices:
        create_pdf(inv)
    print("All 4 fictitious invoices generated successfully!")
