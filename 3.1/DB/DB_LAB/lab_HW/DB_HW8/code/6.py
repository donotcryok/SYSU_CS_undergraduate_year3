#任务6：打印所有图书和读者数据
import pymssql

def print_all_data():
    """打印所有图书和读者数据"""
    try:
        # 连接数据库
        conn = pymssql.connect(server='FORTUNE', database='JY', port=1433)
        cursor = conn.cursor()
        print("数据库连接成功!")
        
        # 打印图书表数据
        print("任务6结果：图书表所有数据")
        print("=" * 60)
        cursor.execute("SELECT * FROM book")
        books = cursor.fetchall()
        
        if books:
            for book in books:
                print(f"图书ID: {book[0]}, 书名: {book[1]}, 价格: {book[2]}")
            print(f"图书表共有 {len(books)} 条记录")
        else:
            print("图书表中没有数据")
        
        # 打印读者表数据
        print("\n任务6结果：读者表所有数据")
        print("=" * 60)
        cursor.execute("SELECT * FROM reader")
        readers = cursor.fetchall()
        
        if readers:
            for reader in readers:
                print(f"读者ID: {reader[0]}, 姓名: {reader[1]}, 性别: {reader[2]}, 部门: {reader[3]}")
            print(f"读者表共有 {len(readers)} 条记录")
        else:
            print("读者表中没有数据")
            
        print("=" * 60)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"任务6执行失败: {e}")
        return False

if __name__ == "__main__":
    print_all_data()