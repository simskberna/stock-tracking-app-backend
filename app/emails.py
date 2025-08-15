import asyncio
from typing import List
from app.services.email_service import gmail_email_service
from app.repositories.user_repository import UserRepository
from app.database import AsyncSessionLocal

async def send_bulk_test_email(critical_products: List):
    """
    Kritik stokta olan ürünler için özelleştirilmiş email bildirimi gönderir.
    single_product_mode=True ise sadece güncellenen ürün bazlı çalışır.
    """
    if not critical_products:
        print("✅ No critical products to send email for.")
        return False

    try:
        async with AsyncSessionLocal() as db:
            user_repo = UserRepository(db)
            emails = await user_repo.get_all_user_emails()

            if not emails:
                print("❌ No user emails found for critical stock notification.")
                return False

            # Email içeriğini hazırla
            products_html = ""
            for product in critical_products:
                status_color = "#d32f2f" if product.stock == 0 else "#ff9800"
                products_html += f"""
                <div style="background-color: #fff3e0; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid {status_color};">
                    <h4 style="margin: 0; color: #e65100;">{product.name}</h4>
                    <p style="margin: 5px 0;"><strong>Current Stock:</strong> <span style="color: {status_color}; font-weight: bold;">{product.stock}</span></p>
                    <p style="margin: 5px 0;"><strong>Critical Level:</strong> {product.critical_stock}</p>
                    <p style="margin: 5px 0;"><strong>Price:</strong> ${product.price}</p>
                </div>
                """

            subject = f"🚨 URGENT: {len(critical_products)} Products at Critical Stock Level"
            body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
                <h2 style="color: #d32f2f; text-align: center;">🚨 Critical Stock Alert</h2>

                <div style="background-color: #ffebee; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #c62828; margin-top: 0;">Immediate Action Required</h3>
                    <p>The following <strong>{len(critical_products)} product(s)</strong> have reached critical stock levels and require immediate restocking:</p>
                </div>

                <h3 style="color: #1976d2;">Critical Products:</h3>
                {products_html}

                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    <h3 style="color: #2e7d32; margin-top: 0;">Recommended Actions:</h3>
                    <ul style="color: #424242;">
                        <li>Review supplier availability for these products</li>
                        <li>Place urgent restock orders</li>
                        <li>Consider temporarily adjusting sales strategies</li>
                        <li>Update customers about potential delays</li>
                    </ul>
                </div>

                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #666; font-size: 14px;">
                        This is an automated critical stock alert from your Stock Management System.<br>
                        Generated on {asyncio.get_event_loop().time()}
                    </p>
                </div>
            </div>
            """

            # Email gönderimi
            await gmail_email_service.send_bulk_email(
                recipients=emails,
                subject=subject,
                body=body,
                is_html=True
            )

            print(f"✅ Critical stock email notification sent to {len(emails)} users")
            return True

    except Exception as e:
        print(f"❌ Failed to send critical stock email notification: {e}")
        return False
