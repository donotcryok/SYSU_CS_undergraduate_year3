#任务3：查询价格高于50的书籍
import pymssql

def query_expensive_books():
    """查询价格高于50的书籍"""
    try:
        # 连接数据库
        conn = pymssql.connect(server='FORTUNE', database='JY', port=1433)
        cursor = conn.cursor()
        print("数据库连接成功!")
        
        # 查询价格高于50的书籍
        sql = "SELECT * FROM book WHERE book_price > 50"
        cursor.execute(sql)
        books = cursor.fetchall()
        
        print("任务3结果：价格高于50的书籍")
        print("=" * 60)
        
        if books:
            for book in books:
                print(f"图书ID: {book[0]}, 书名: {book[1]}, 价格: {book[2]}")
            print(f"共找到 {len(books)} 本价格高于50的书籍")
        else:
            print("没有找到价格高于50的书籍")
            
        print("=" * 60)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"任务3执行失败: {e}")
        return False

if __name__ == "__main__":
    query_expensive_books()