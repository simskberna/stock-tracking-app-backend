from typing import Dict, Any
from app.services.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)


async def handle_critical_stock_notification(data: Dict[str, Any]):
    """Kritik stok durumunda tüm kullanıcılara bildirim gönder"""
    product_name = data.get('product_name')
    stock_level = data.get('stock_level')
    critical_level = data.get('critical_level')

    # WebSocket mesajı
    ws_message = {
        "type": "critical_stock",
        "data": {
            "product_name": product_name,
            "stock_level": stock_level,
            "critical_level": critical_level,
            "message": f"Product '{product_name}' stock is critical: {stock_level}",
            "timestamp": data.get('timestamp')
        }
    }

    # Email içeriği
    email_subject = f"🚨 Critical Stock Alert - {product_name}"
    email_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .alert {{ background-color: #fee; border: 1px solid #fcc; border-radius: 5px; padding: 15px; margin: 20px 0; }}
            .product-name {{ color: #d63384; font-weight: bold; }}
            .stock-info {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 0.9em; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="color: #dc3545;">🚨 Critical Stock Alert</h2>

            <div class="alert">
                <p><strong>Attention:</strong> One of your products has reached a critical stock level!</p>
            </div>

            <div class="stock-info">
                <h3>Product Details:</h3>
                <ul>
                    <li><strong>Product Name:</strong> <span class="product-name">{product_name}</span></li>
                    <li><strong>Current Stock:</strong> <span style="color: #dc3545; font-weight: bold;">{stock_level} units</span></li>
                    <li><strong>Critical Level:</strong> {critical_level} units</li>
                </ul>
            </div>

            <p><strong>Action Required:</strong> Please restock this item as soon as possible to avoid stockouts.</p>

            <div class="footer">
                <p>This is an automated notification from your Stock Management System.</p>
                <p>If you have any questions, please contact your system administrator.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Tüm kullanıcılara bildirim gönder
    await notification_service.send_notification_to_all_users(
        ws_message=ws_message,
        email_subject=email_subject,
        email_body=email_body,
        send_email=True
    )


async def handle_user_login_notification(data: Dict[str, Any]):
    """Kullanıcı login olduğunda bildirim (sadece log)"""
    user_email = data.get('user_email')
    login_time = data.get('login_time')

    logger.info(f"User {user_email} logged in at {login_time}")


async def handle_user_logout_notification(data: Dict[str, Any]):
    """Kullanıcı logout olduğunda bildirim (sadece log)"""
    user_email = data.get('user_email')
    logout_time = data.get('logout_time')

    logger.info(f"User {user_email} logged out at {logout_time}")
