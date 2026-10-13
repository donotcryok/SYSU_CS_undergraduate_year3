@echo off
REM 性能测试脚本 - 运行尾递归消除性能对比测试
REM 编译原理实验：后缀表达式 Postfix

REM 切换到项目根目录
cd /d "%~dp0.."

echo ========================================
echo   尾递归消除性能对比测试
echo ========================================
echo.

REM 检查编译后的类是否存在
if not exist bin\PerformanceTest.class (
    echo 正在编译...
    call scripts\build.bat
)

echo 运行性能测试...
echo.

java -cp bin PerformanceTest

echo.
echo ========================================
echo   性能测试完成
echo ========================================
echo.
echo 提示: CSV 数据已保存到 data/perf_results.csv
echo       可运行 python scripts/plot_perf.py 生成图表
echo.
pause