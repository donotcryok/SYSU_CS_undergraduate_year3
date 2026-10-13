/*
========================================================================
补丁名称：Patch_Add_Indexes.sql
功能：
1. 确保 Orders 表有时间字段（用于按日期查询的索引优化）。
2. 为“车牌号”、“运单日期”、“司机ID”创建非聚集索引。
========================================================================
*/

USE LogisticsDB;
GO

-- 1. 预处理：检查 Orders 表是否有 'OrderTime' 字段
--    (如果没有，必须先添加，否则无法建立日期索引)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Orders') AND name = 'OrderTime')
BEGIN
    PRINT '正在添加 OrderTime 字段...';
    ALTER TABLE Orders ADD OrderTime DATETIME DEFAULT GETDATE();
    -- 将旧数据的 OrderTime 填充为当前时间，避免 NULL
    EXEC('UPDATE Orders SET OrderTime = GETDATE() WHERE OrderTime IS NULL');
END
GO

-- 2. 索引优化一：车牌号 (Vehicle.PlateNumber)
--    对应要求：高频查询字段“车牌号”
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Vehicle_PlateNumber')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Vehicle_PlateNumber 
    ON Vehicle(PlateNumber);
    PRINT '已创建索引：IX_Vehicle_PlateNumber (优化按车牌查询)';
END
ELSE
BEGIN
    PRINT 'ℹ索引 IX_Vehicle_PlateNumber 已存在，跳过。';
END
GO

-- 3. 索引优化二：运单日期 (Orders.OrderTime)
--    对应要求：高频查询字段“运单日期”
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Orders_OrderTime')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Orders_OrderTime 
    ON Orders(OrderTime);
    PRINT '已创建索引：IX_Orders_OrderTime (优化按日期筛选运单)';
END
ELSE
BEGIN
    PRINT 'ℹ索引 IX_Orders_OrderTime 已存在，跳过。';
END
GO

-- 4. 索引优化三：司机关联查询 (Abnormality.DriverID)
--    对应要求：高频查询字段“司机工号” (优化外键查询)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Abnormality_DriverID')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Abnormality_DriverID 
    ON Abnormality(DriverID);
    PRINT '已创建索引：IX_Abnormality_DriverID (优化查询某司机的异常记录)';
END
ELSE
BEGIN
    PRINT 'ℹ索引 IX_Abnormality_DriverID 已存在，跳过。';
END
GO

PRINT '------------------------------------------------';
PRINT '索引补丁执行完毕！所有高频字段索引已建立。';