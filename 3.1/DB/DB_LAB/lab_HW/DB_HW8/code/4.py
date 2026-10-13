# 任务4：查询信息工程系的读者
import pymssql

def query_info_engineering_readers():
    """查询信息工程系的读者"""
    try:
        # 连接数据库
        conn = pymssql.connect(server='FORTUNE', database='JY', port=1433)
        cursor = conn.cursor()
        print("数据库连接成功!")
        
        # 查询信息工程系的读者 - 使用正确的列名
        sql = "SELECT * FROM reader WHERE reader_department = '信息工程系'"
        cursor.execute(sql)
        readers = cursor.fetchall()
        
        print("任务4结果：信息工程系的读者")
        print("=" * 60)
        
        if readers:
            for reader in readers:
                print(f"读者ID: {reader[0]}, 姓名: {reader[1]}, 性别: {reader[2]}, 部门: {reader[3]}")
            print(f"共找到 {len(readers)} 位信息工程系的读者")
        else:
            print("没有找到信息工程系的读者")
            
        print("=" * 60)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"任务4执行失败: {e}")
        return False

if __name__ == "__main__":
    query_info_engineering_readers()