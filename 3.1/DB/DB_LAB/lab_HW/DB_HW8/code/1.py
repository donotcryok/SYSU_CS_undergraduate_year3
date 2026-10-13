# 在reader表增加一条数据
import pymssql

def add_reader():
    """添加读者记录"""
    try:
        # 连接数据库
        conn = pymssql.connect(server='FORTUNE', database='JY', port=1433)
        cursor = conn.cursor()
        print("数据库连接成功!")
        
        sql = "INSERT INTO reader (reader_id, reader_name, reader_sex, reader_department) VALUES (%s, %s, %s, %s)"
        values = ('r0020', '王小明', '男', '临床医学系')
        cursor.execute(sql, values)
        conn.commit()
        
        print("任务1：成功添加读者记录")
        print(f"添加的数据: reader_id='r0020', reader_name='王小明', reader_sex='男', reader_department='临床医学系'")
        
        # 验证插入结果
        cursor.execute("SELECT * FROM reader WHERE reader_id = 'r0020'")
        result = cursor.fetchone()
        print(f"验证结果: {result}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"任务1执行失败: {e}")
        return False

if __name__ == "__main__":
    add_reader()