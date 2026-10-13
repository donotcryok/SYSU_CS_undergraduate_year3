import pymssql

def test_connection():
    try:
        conn = pymssql.connect(server='FORTUNE', database='JY')
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()
        print(f"连接成功! SQL Server版本: {version[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"连接失败: {e}")
        return False

if __name__ == "__main__":
    test_connection()