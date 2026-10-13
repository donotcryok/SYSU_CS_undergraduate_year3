# 任务5：删除读者记录
import pymssql

def delete_reader():
    """删除读者记录"""
    try:
        # 连接数据库
        conn = pymssql.connect(server='FORTUNE', database='JY', port=1433)
        cursor = conn.cursor()
        print("数据库连接成功!")
        
        # 先确认要删除的记录存在
        cursor.execute("SELECT * FROM reader WHERE reader_id = 'r0020'")
        reader = cursor.fetchone()
        
        if reader:
            print(f"找到要删除的读者记录: {reader}")
            
            # 删除读者记录
            sql = "DELETE FROM reader WHERE reader_id = %s"
            cursor.execute(sql, ('r0020',))
            conn.commit()
            
            print("任务5完成：成功删除读者记录")
            print(f"已删除读者ID为'r0020'的记录")
            
            # 验证删除结果
            cursor.execute("SELECT * FROM reader WHERE reader_id = 'r0020'")
            result = cursor.fetchone()
            if not result:
                print("确认读者记录已成功删除")
            else:
                print("警告：读者记录可能未成功删除")
        else:
            print("未找到读者记录r0020，无需删除")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"任务5执行失败: {e}")
        return False

if __name__ == "__main__":
    delete_reader()