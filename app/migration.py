#import psycopg2
#conn = psycopg2.connect(
#    dbname="stock_db",
#    user="admin",
#    password="root",
#    host="localhost",
#    port="5432"
#)
#cur = conn.cursor()
#cur.execute("ALTER TABLE orders ADD COLUMN price FLOAT;")
#conn.commit()

import asyncpg


async def delete_orders_only_db():
    # Direkt PostgreSQL bağlantısı (SQLAlchemy bypas)
    conn = await asyncpg.connect("postgresql://admin:root@localhost:5432/stock_db")

    # DELETE işlemi
    result = await conn.execute("DELETE FROM orders")
    print(f"Deleted {result} rows")

    # Kontrol
    count = await conn.fetchval("SELECT COUNT(*) FROM orders")
    print(f"Remaining orders: {count}")

    await conn.close()


# Çalıştır
import asyncio

asyncio.run(delete_orders_only_db())