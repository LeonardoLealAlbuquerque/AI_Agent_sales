import sys
import os
from datetime import date, timedelta

# Adiciona o diretório raiz ao path para permitir as importações do pacote 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.models.order import Order, OrderStatus

def popular_banco():
    print("⚙️ Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        if db.query(Client).first():
            print("⚠️ O banco já possui dados. Execução ignorada.")
            return

        hoje = date.today()
        print("⏳ Injetando cenário demonstrativo (Seed Demo)...")

        # Cliente 1: Risco Baixo
        c1 = Client(company_name="Tech Solutions B2B", cnpj="12345678000199", credit_limit=50000.0, status="ACTIVE")
        # Cliente 2: Risco Alto (Inadimplente)
        c2 = Client(company_name="Risco Elevado LTDA", cnpj="98765432000188", credit_limit=10000.0, status="ACTIVE")
        db.add_all([c1, c2])
        db.commit()

        # Faturas
        f_pendente = Invoice(client_id=c1.id, amount=2500.0, due_date=hoje + timedelta(days=10), status=InvoiceStatus.PENDING)
        f_vencida = Invoice(client_id=c2.id, amount=1500.0, due_date=hoje - timedelta(days=35), status=InvoiceStatus.PENDING)
        db.add_all([f_pendente, f_vencida])

        # Pedidos
        pedido = Order(client_id=c1.id, status=OrderStatus.PENDING, total_amount=1500.0, created_at=hoje, estimated_delivery_date=hoje + timedelta(days=5))
        db.add(pedido)

        db.commit()
        print("✅ Banco populado com sucesso para a homologação do Agente de IA!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao popular o banco: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco()