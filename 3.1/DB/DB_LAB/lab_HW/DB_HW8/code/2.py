# 任务2：更新读者部门信息
import pymssql

def update_reader_department():
    """更新读者部门信息"""
    try:
        # 连接数据库
        conn = pymssql.connect(server='FORTUNE', database='JY', port=1433)
        cursor = conn.cursor()
        print("数据库连接成功!")
        
        sql = "UPDATE reader SET reader_department = %s WHERE reader_id = %s"
        values = ('护理系', 'r0020')
        cursor.execute(sql, values)
        conn.commit()
        
        print("任务2：成功更新读者部门")
        print(f"将读者'r0020'的部门从'临床医学系'更新为'护理系'")
        
        # 验证更新结果
        cursor.execute("SELECT * FROM reader WHERE reader_id = 'r0020'")
        result = cursor.fetchone()
        print(f"更新后的读者信息: {result}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"任务2执行失败: {e}")
        return False

if __name__ == "__main__":
    update_reader_department()