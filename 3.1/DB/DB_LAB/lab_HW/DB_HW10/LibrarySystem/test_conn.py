import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=FORTUNE,1433;"
    "DATABASE=JY;"
    "Trusted_Connection=yes;"
)
print("尝试连接：", conn_str)
try:
    conn = pyodbc.connect(conn_str, timeout=5)
    cur = conn.cursor()
    cur.execute("SELECT TOP 3 book_id, book_name, book_price FROM book")
    rows = cur.fetchall()
    print("查询结果样例（最多3条）：")
    for r in rows:
        print(r)
    conn.close()
    print("连接与查询成功")
except Exception as e:
    print("连接或查询失败，错误：", e)