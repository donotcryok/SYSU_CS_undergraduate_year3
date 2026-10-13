import pyodbc

class DatabaseManager:
    def __init__(self):
        # 数据库连接字符串配置
        # DRIVER: 指定驱动程序
        # SERVER: 服务器地址 (localhost)
        # DATABASE: 数据库名 (LogisticsDB)
        # Trusted_Connection: 使用 Windows 身份验证
        self.conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=LogisticsDB;"
            "Trusted_Connection=yes;"
        )
        self.conn = None

    def connect(self):
        """建立数据库连接"""
        try:
            self.conn = pyodbc.connect(self.conn_str)
            print("数据库连接成功！")
            return True
        except pyodbc.Error as e:
            print(f"数据库连接失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    # --- 模块 A: 运单分配相关 ---

    def get_idle_vehicles(self):
        """获取所有状态为'空闲'的车辆"""
        if not self.conn: return []
        cursor = self.conn.cursor()
        try:
            # 假设 Status 字段存储的是字符串 '空闲'
            cursor.execute("SELECT VehicleID, PlateNumber FROM Vehicle WHERE CurrentStatus = '空闲'")
            return cursor.fetchall()
        except pyodbc.Error as e:
            print(f"查询空闲车辆失败: {e}")
            return []

    def create_order(self, weight, volume, destination, vehicle_id):
        """创建新运单"""
        if not self.conn: return
        cursor = self.conn.cursor()
        # 注意：这里不捕获异常，而是让异常抛出给 GUI 层处理，以便捕获触发器错误
        # Status 默认为 '待分配' 或 '运输中'，根据业务逻辑，分配了车辆通常是运输中，这里设为'待分配'或由触发器处理
        sql = "INSERT INTO Orders (Weight, Volume, Destination, Status, VehicleID) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(sql, (weight, volume, destination, '待分配', vehicle_id))
        self.conn.commit()

    # --- 模块 B: 基础信息录入相关 ---

    def get_fleets(self):
        """获取所有车队信息用于下拉框"""
        if not self.conn: return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT FleetID, FleetName FROM Fleet")
        return cursor.fetchall()

    def add_driver(self, name, license_grade, phone, fleet_id):
        """添加新司机"""
        if not self.conn: return False
        cursor = self.conn.cursor()
        try:
            sql = "INSERT INTO Driver (Name, LicenseGrade, Phone, FleetID) VALUES (?, ?, ?, ?)"
            cursor.execute(sql, (name, license_grade, phone, fleet_id))
            self.conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"添加司机失败: {e}")
            return False

    def add_vehicle(self, plate_number, max_weight, max_volume, fleet_id):
        """添加新车辆"""
        if not self.conn: return False
        cursor = self.conn.cursor()
        try:
            # 新车默认状态为 '空闲'
            sql = "INSERT INTO Vehicle (PlateNumber, MaxWeight, MaxVolume, CurrentStatus, FleetID) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(sql, (plate_number, max_weight, max_volume, '空闲', fleet_id))
            self.conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"添加车辆失败: {e}")
            return False

    # --- 模块 C: 异常与状态管理相关 ---

    def get_all_vehicles(self):
        """获取所有车辆用于异常录入"""
        if not self.conn: return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT VehicleID, PlateNumber FROM Vehicle")
        return cursor.fetchall()

    def get_all_drivers(self):
        """获取所有司机用于异常录入"""
        if not self.conn: return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT DriverID, Name FROM Driver")
        return cursor.fetchall()

    def add_abnormality(self, event_type, occur_time, fine_amount, driver_id, vehicle_id):
        """录入异常记录"""
        if not self.conn: return False
        cursor = self.conn.cursor()
        try:
            # IsHandled 默认为 0 (False)
            sql = "INSERT INTO Abnormality (EventType, OccurTime, FineAmount, IsHandled, DriverID, VehicleID) VALUES (?, ?, ?, ?, ?, ?)"
            cursor.execute(sql, (event_type, occur_time, fine_amount, 0, driver_id, vehicle_id))
            self.conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"录入异常失败: {e}")
            return False

    # --- 模块 D: 报表查询相关 ---

    def get_weekly_abnormalities(self):
        """查询每周异常视图"""
        if not self.conn: return [], []
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM View_WeeklyAbnormalities")
            rows = cursor.fetchall()
            # 获取列名
            columns = [column[0] for column in cursor.description]
            return columns, rows
        except pyodbc.Error as e:
            print(f"查询视图失败: {e}")
            return [], []
    # --- 新增功能：运单签收相关 ---

    def get_active_orders(self):
        """获取所有处于 '待分配' 或 '运输中' 的运单"""
        if not self.conn: return []
        cursor = self.conn.cursor()
        try:
            # 关联 Vehicle 表显示车牌号
            sql = """
            SELECT o.OrderID, o.Destination, o.Weight, v.PlateNumber, o.Status 
            FROM Orders o
            JOIN Vehicle v ON o.VehicleID = v.VehicleID
            WHERE o.Status != '已完成'
            """
            cursor.execute(sql)
            return cursor.fetchall()
        except pyodbc.Error as e:
            print(f"查询活跃运单失败: {e}")
            return []

    def complete_order(self, order_id):
        """签收运单 (将状态改为 '已完成')"""
        if not self.conn: return False
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE Orders SET Status = '已完成' WHERE OrderID = ?", (order_id,))
            self.conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"签收失败: {e}")
            return False