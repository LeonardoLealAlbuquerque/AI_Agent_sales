from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base 

class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    
    # Chaves estrangeiras essenciais para um item de pedido
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    
    # Campos solicitados na task
    quantidade = Column(Integer, nullable=False, default=1)
    desconto = Column(Float, nullable=False, default=0.0)
    subtotal = Column(Float, nullable=False, default=0.0)

    # Relacionamentos (Descomente e ajuste conforme os seus outros modelos)
    # pedido = relationship("Pedido", back_populates="itens")
    # produto = relationship("Produto")