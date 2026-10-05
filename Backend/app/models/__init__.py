# Importando os Enums (se você criou o ClientStatus no client.py, adicione-o aqui)
from app.models.order import OrderStatus

# Importando os Modelos
from app.models.client import Client
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.invoice import Invoice
from app.models.credit_limit_request import CreditLimitRequest
from app.models.conversation import Conversation
from app.models.chat_message import ChatMessageRecord

# O __all__ diz explicitamente ao Python o que está sendo exportado por este pacote.
# Facilita o autocomplete e protege a importação com asterisco (*).
__all__ = [
    "Client",
    "Order",
    "OrderStatus",
    "OrderItem",
    "Invoice",
    "CreditLimitRequest",
    "Conversation",
    "ChatMessageRecord",
]