USE LogisticsDB;
GO

IF COL_LENGTH('Orders', 'DriverID') IS NULL
BEGIN
    ALTER TABLE Orders ADD DriverID INT NULL;
END;
GO

IF COL_LENGTH('Orders', 'OrderTime') IS NULL
BEGIN
    ALTER TABLE Orders ADD OrderTime DATETIME NULL;
END;
GO

IF COL_LENGTH('Orders', 'OrderTime') IS NOT NULL
BEGIN
    EXEC sp_executesql N'UPDATE Orders SET OrderTime = GETDATE() WHERE OrderTime IS NULL';
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Orders_Driver')
BEGIN
    ALTER TABLE Orders WITH NOCHECK
    ADD CONSTRAINT FK_Orders_Driver FOREIGN KEY (DriverID) REFERENCES Driver(DriverID);
END;
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
        AND MONTH(a.OccurTime) = @Month AND YEAR(a.OccurTime) = @Year
    WHERE f.FleetID = @FleetID
    GROUP BY f.FleetName;
END;
GO

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

    UPDATE Vehicle 
    SET CurrentStatus = '运输中' 
    WHERE VehicleID = @VehicleID;
END;
GO

IF OBJECT_ID('trg_DriverAudit', 'TR') IS NOT NULL DROP TRIGGER trg_DriverAudit;
GO
CREATE TRIGGER trg_DriverAudit
ON Driver
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF UPDATE(LicenseGrade)
    BEGIN
        INSERT INTO History_Log (TableName, RecordID, OperationType, OldValue, NewValue)
        SELECT 
            'Driver', 
            d.DriverID, 
            'Update_License', 
            d.LicenseGrade,
            i.LicenseGrade
        FROM deleted d
        INNER JOIN inserted i ON d.DriverID = i.DriverID;
    END
END;
GO

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

    IF NOT EXISTS (SELECT 1 FROM Orders WHERE VehicleID = @VehicleID AND Status <> '已完成')
    BEGIN
        UPDATE Vehicle SET CurrentStatus = '空闲' WHERE VehicleID = @VehicleID;
    END
END;
GO