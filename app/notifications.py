from app.websocket_manager import manager

async def notify_critical_stock(user_email: str, product):
    if product.stock <= product.critical_stock:
        message = {
            "type": "critical_stock",
            "product_id": product.id,
            "name": product.name,
            "stock": product.stock,
            "critical_stock": product.critical_stock,
        }
        await manager.send_personal_message(user_email, message)
