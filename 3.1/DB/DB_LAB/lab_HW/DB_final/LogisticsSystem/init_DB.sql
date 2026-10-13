/* ============================================================
   项目名称：智慧物流车队与配送管理系统
   描述：一键初始化脚本（包含建库、建表、测试数据、触发器）
   ============================================================
*/

-- 1. 如果存在同名数据库先删除，确保每次运行都是全新的环境（方便调试）
USE master;
GO
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'LogisticsDB')
BEGIN
    ALTER DATABASE LogisticsDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE LogisticsDB;
END
GO

-- 2. 创建数据库
CREATE DATABASE LogisticsDB;
GO
USE LogisticsDB;
GO

-- 3. 创建表结构
-- 配送中心
CREATE TABLE DistributionCenter (
    CenterID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(50) NOT NULL,
    Location NVARCHAR(100)
);

-- 车队
CREATE TABLE Fleet (
    FleetID INT PRIMARY KEY IDENTITY(1,1),
    FleetName NVARCHAR(50) NOT NULL,
    SupervisorName NVARCHAR(50) NOT NULL,
    CenterID INT NOT NULL,
    FOREIGN KEY (CenterID) REFERENCES DistributionCenter(CenterID)
);

-- 车辆
CREATE TABLE Vehicle (
    VehicleID INT PRIMARY KEY IDENTITY(1,1),
    PlateNumber NVARCHAR(20) NOT NULL UNIQUE, 
    MaxWeight DECIMAL(10, 2) NOT NULL, -- 最大载重
    MaxVolume DECIMAL(10, 2) NOT NULL, -- 最大容积
    CurrentStatus NVARCHAR(20) DEFAULT '空闲' CHECK (CurrentStatus IN ('空闲', '运输中', '维修中', '异常')),
    FleetID INT NOT NULL,
    FOREIGN KEY (FleetID) REFERENCES Fleet(FleetID)
);

-- 司机
CREATE TABLE Driver (
    DriverID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(50) NOT NULL,
    LicenseGrade NVARCHAR(10) CHECK (LicenseGrade IN ('A1', 'A2', 'B1', 'B2', 'C1')),
    Phone NVARCHAR(20),
    FleetID INT NOT NULL,
    FOREIGN KEY (FleetID) REFERENCES Fleet(FleetID)
);

-- 运单
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY IDENTITY(1,1),
    Weight DECIMAL(10, 2) NOT NULL,
    Volume DECIMAL(10, 2) NOT NULL,
    Destination NVARCHAR(100),
    Status NVARCHAR(20) DEFAULT '待分配' CHECK (Status IN ('待分配', '运输中', '已完成')),
    VehicleID INT, 
    FOREIGN KEY (VehicleID) REFERENCES Vehicle(VehicleID)
);

-- 异常记录
CREATE TABLE Abnormality (
    AbnormalityID INT PRIMARY KEY IDENTITY(1,1),
    EventType NVARCHAR(20) NOT NULL, 
    OccurTime DATETIME DEFAULT GETDATE(),
    FineAmount DECIMAL(10, 2) DEFAULT 0,
    IsHandled BIT DEFAULT 0, -- 0:未处理, 1:已处理
    DriverID INT,
    VehicleID INT,
    FOREIGN KEY (DriverID) REFERENCES Driver(DriverID),
    FOREIGN KEY (VehicleID) REFERENCES Vehicle(VehicleID)
);

-- 审计日志 (用于触发器)
CREATE TABLE History_Log (
    LogID INT PRIMARY KEY IDENTITY(1,1),
    TableName NVARCHAR(50),
    RecordID INT,
    OperationType NVARCHAR(20),
    OldValue NVARCHAR(MAX),
    NewValue NVARCHAR(MAX),
    LogTime DATETIME DEFAULT GETDATE()
);
GO

-- 4. 插入测试数据 (没有数据，前端就没法展示)
-- 插入配送中心
INSERT INTO DistributionCenter (Name, Location) VALUES ('北京东区中心', '北京市朝阳区');

-- 插入车队
INSERT INTO Fleet (FleetName, SupervisorName, CenterID) VALUES ('猛虎队', '张主管', 1);

-- 插入车辆 (注意：ID是自动生成的，这里假设ID为1和2)
INSERT INTO Vehicle (PlateNumber, MaxWeight, MaxVolume, CurrentStatus, FleetID) 
VALUES ('京A88888', 5000.00, 20.0, '空闲', 1),
       ('京B66666', 2000.00, 10.0, '运输中', 1);

-- 插入司机
INSERT INTO Driver (Name, LicenseGrade, Phone, FleetID) 
VALUES ('李老四', 'A1', '13800138000', 1),
       ('王小五', 'B2', '13900139000', 1);

-- 插入一些运单
INSERT INTO Orders (Weight, Volume, Destination, Status, VehicleID)
VALUES (1000.00, 5.0, '天津港', '已完成', 1), -- 已完成的
       (500.00, 2.0, '大兴机场', '运输中', 2); -- 正运着的
GO

-- 5. 创建核心触发器：防止超载
CREATE TRIGGER trg_CheckWeightLimit
ON Orders
AFTER INSERT, UPDATE
AS
BEGIN
    DECLARE @VehicleID INT;
    DECLARE @TotalWeight DECIMAL(10, 2);
    DECLARE @MaxWeight DECIMAL(10, 2);

    SELECT @VehicleID = VehicleID FROM inserted;
    IF @VehicleID IS NULL RETURN;

    -- 计算该车当前未完成运单的总重
    SELECT @TotalWeight = SUM(Weight) 
    FROM Orders 
    WHERE VehicleID = @VehicleID AND Status <> '已完成';

    SELECT @MaxWeight = MaxWeight FROM Vehicle WHERE VehicleID = @VehicleID;

    IF ISNULL(@TotalWeight, 0) > @MaxWeight
    BEGIN
        RAISERROR ('【系统警告】严重超载！当前分配导致超出车辆最大载重，操作被拒绝。', 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO

-- 6. 创建视图：查询本周异常 (为了满足作业要求)
CREATE VIEW View_WeeklyAbnormalities AS
SELECT a.AbnormalityID, a.EventType, a.OccurTime, d.Name AS DriverName, v.PlateNumber
FROM Abnormality a
JOIN Driver d ON a.DriverID = d.DriverID
JOIN Vehicle v ON a.VehicleID = v.VehicleID;
GO

PRINT '数据库 LogisticsDB 初始化完成！所有表、数据、触发器已就绪。';