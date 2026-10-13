USE master;
GO
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'LogisticsDB')
BEGIN
    ALTER DATABASE LogisticsDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE LogisticsDB;
END
GO

CREATE DATABASE LogisticsDB;
GO
USE LogisticsDB;
GO

CREATE TABLE DistributionCenter (
    CenterID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(50) NOT NULL,
    Location NVARCHAR(100)
);

CREATE TABLE Fleet (
    FleetID INT PRIMARY KEY IDENTITY(1,1),
    FleetName NVARCHAR(50) NOT NULL,
    SupervisorName NVARCHAR(50) NOT NULL,
    CenterID INT NOT NULL,
    FOREIGN KEY (CenterID) REFERENCES DistributionCenter(CenterID)
);

CREATE TABLE Vehicle (
    VehicleID INT PRIMARY KEY IDENTITY(1,1),
    PlateNumber NVARCHAR(20) NOT NULL UNIQUE, 
    MaxWeight DECIMAL(10, 2) NOT NULL,
    MaxVolume DECIMAL(10, 2) NOT NULL,
    CurrentStatus NVARCHAR(20) DEFAULT '空闲' CHECK (CurrentStatus IN ('空闲', '运输中', '维修中', '异常')),
    FleetID INT NOT NULL,
    FOREIGN KEY (FleetID) REFERENCES Fleet(FleetID)
);

CREATE TABLE Driver (
    DriverID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(50) NOT NULL,
    LicenseGrade NVARCHAR(10) CHECK (LicenseGrade IN ('A1', 'A2', 'B1', 'B2', 'C1')),
    Phone NVARCHAR(20),
    FleetID INT NOT NULL,
    FOREIGN KEY (FleetID) REFERENCES Fleet(FleetID)
);

CREATE TABLE Orders (
    OrderID INT PRIMARY KEY IDENTITY(1,1),
    Weight DECIMAL(10, 2) NOT NULL,
    Volume DECIMAL(10, 2) NOT NULL,
    Destination NVARCHAR(100),
    Status NVARCHAR(20) DEFAULT '待分配' CHECK (Status IN ('待分配', '运输中', '已完成')),
    VehicleID INT, 
    DriverID INT NULL,
    OrderTime DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (VehicleID) REFERENCES Vehicle(VehicleID),
    FOREIGN KEY (DriverID) REFERENCES Driver(DriverID)
);

CREATE TABLE Abnormality (
    AbnormalityID INT PRIMARY KEY IDENTITY(1,1),
    EventType NVARCHAR(20) NOT NULL, 
    OccurTime DATETIME DEFAULT GETDATE(),
    FineAmount DECIMAL(10, 2) DEFAULT 0,
    IsHandled BIT DEFAULT 0,
    DriverID INT,
    VehicleID INT,
    FOREIGN KEY (DriverID) REFERENCES Driver(DriverID),
    FOREIGN KEY (VehicleID) REFERENCES Vehicle(VehicleID)
);

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

INSERT INTO DistributionCenter (Name, Location) VALUES ('中山大学计算机学院', '广州市番禺区');

INSERT INTO Fleet (FleetName, SupervisorName, CenterID) VALUES ('院楼车队', '张主管', 1);

INSERT INTO Vehicle (PlateNumber, MaxWeight, MaxVolume, CurrentStatus, FleetID) 
VALUES ('粤A88888', 5000.00, 20.0, '空闲', 1),
       ('粤B66666', 2000.00, 10.0, '运输中', 1);

INSERT INTO Driver (Name, LicenseGrade, Phone, FleetID) 
VALUES ('李老四', 'A1', '13800138000', 1),
       ('王小五', 'B2', '13900139000', 1);

INSERT INTO Orders (Weight, Volume, Destination, Status, VehicleID, DriverID, OrderTime)
VALUES (1000.00, 5.0, '香港', '已完成', 1, 1, DATEADD(day, -10, GETDATE())),
    (500.00, 2.0, '白云机场', '运输中', 2, 2, DATEADD(day, -2, GETDATE()));
GO

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

CREATE VIEW View_WeeklyAbnormalities AS
SELECT a.AbnormalityID, a.EventType, a.OccurTime, d.Name AS DriverName, v.PlateNumber
FROM Abnormality a
JOIN Driver d ON a.DriverID = d.DriverID
JOIN Vehicle v ON a.VehicleID = v.VehicleID;
GO

IF OBJECT_ID('sp_GetFleetMonthlyReport', 'P') IS NOT NULL DROP PROCEDURE sp_GetFleetMonthlyReport;
GO
CREATE PROCEDURE sp_GetFleetMonthlyReport
    @FleetID INT,
    @Year INT,
    @Month INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT 
        f.FleetName,
        COUNT(DISTINCT o.OrderID) AS TotalOrders,
        COUNT(DISTINCT a.AbnormalityID) AS TotalAbnormalities,
        ISNULL(SUM(a.FineAmount), 0) AS TotalFines
    FROM Fleet f
    LEFT JOIN Vehicle v ON f.FleetID = v.FleetID
    LEFT JOIN Orders o ON v.VehicleID = o.VehicleID 
        AND YEAR(o.OrderTime) = @Year AND MONTH(o.OrderTime) = @Month
    LEFT JOIN Abnormality a ON v.VehicleID = a.VehicleID 
        AND YEAR(a.OccurTime) = @Year AND MONTH(a.OccurTime) = @Month
    WHERE f.FleetID = @FleetID
    GROUP BY f.FleetName;
END;
GO

PRINT '数据库 LogisticsDB 初始化完成！所有表、数据、触发器已就绪。';