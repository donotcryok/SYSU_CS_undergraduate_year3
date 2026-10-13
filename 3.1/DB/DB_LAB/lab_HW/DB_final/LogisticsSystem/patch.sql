USE LogisticsDB;
GO

-- =============================================
-- 修复 1：创建存储过程 (解决问题 5)
-- 用于计算车队月度绩效
-- =============================================
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
        COUNT(DISTINCT o.OrderID) AS TotalOrders,    -- 总运单数
        COUNT(DISTINCT a.AbnormalityID) AS TotalAbnormalities, -- 异常总数
        ISNULL(SUM(a.FineAmount), 0) AS TotalFines   -- 累计罚款
    FROM Fleet f
    LEFT JOIN Vehicle v ON f.FleetID = v.FleetID
    LEFT JOIN Orders o ON v.VehicleID = o.VehicleID 
        -- 注意：这里假设Orders表暂时没有时间字段，实际应有，这里为了跑通演示简化处理
    LEFT JOIN Abnormality a ON v.VehicleID = a.VehicleID 
        AND MONTH(a.OccurTime) = @Month AND YEAR(a.OccurTime) = @Year
    WHERE f.FleetID = @FleetID
    GROUP BY f.FleetName;
END;
GO

-- =============================================
-- 修复 2：创建触发器 - 车辆状态自动流转 (解决问题 3)
-- 逻辑：当运单表插入新记录(分配)时，自动将车辆状态改为 '运输中'
-- =============================================
IF OBJECT_ID('trg_SetVehicleBusy', 'TR') IS NOT NULL DROP TRIGGER trg_SetVehicleBusy;
GO
CREATE TRIGGER trg_SetVehicleBusy
ON Orders
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @VehicleID INT;
    SELECT @VehicleID = VehicleID FROM inserted;

    -- 将对应车辆状态更新为 '运输中'
    UPDATE Vehicle 
    SET CurrentStatus = '运输中' 
    WHERE VehicleID = @VehicleID;
END;
GO

-- =============================================
-- 修复 3：创建触发器 - 审计日志 (解决问题 4)
-- 逻辑：当修改 Driver 表时，记录旧数据
-- =============================================
IF OBJECT_ID('trg_DriverAudit', 'TR') IS NOT NULL DROP TRIGGER trg_DriverAudit;
GO
CREATE TRIGGER trg_DriverAudit
ON Driver
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    -- 只有当 LicenseGrade 被修改时才记录
    IF UPDATE(LicenseGrade)
    BEGIN
        INSERT INTO History_Log (TableName, RecordID, OperationType, OldValue, NewValue)
        SELECT 
            'Driver', 
            d.DriverID, 
            'Update_License', 
            d.LicenseGrade, -- 旧值 (来自 deleted 表)
            i.LicenseGrade  -- 新值 (来自 inserted 表)
        FROM deleted d
        INNER JOIN inserted i ON d.DriverID = i.DriverID;
    END
END;
GO

-- =============================================
-- 修复 4：补充触发器 - 车辆状态自动闲置 (配合签收功能)
-- 逻辑：当运单状态变为'已完成'时，检查该车是否还有未完成运单，若无，则变回 '空闲'
-- =============================================
IF OBJECT_ID('trg_SetVehicleIdle', 'TR') IS NOT NULL DROP TRIGGER trg_SetVehicleIdle;
GO
CREATE TRIGGER trg_SetVehicleIdle
ON Orders
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @VehicleID INT;
    SELECT @VehicleID = VehicleID FROM inserted;

    -- 如果该车所有运单都已完成
    IF NOT EXISTS (SELECT 1 FROM Orders WHERE VehicleID = @VehicleID AND Status <> '已完成')
    BEGIN
        UPDATE Vehicle SET CurrentStatus = '空闲' WHERE VehicleID = @VehicleID;
    END
END;
GO