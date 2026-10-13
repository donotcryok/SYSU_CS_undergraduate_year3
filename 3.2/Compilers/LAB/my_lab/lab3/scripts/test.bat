@echo off
REM 单元测试脚本 - 运行 JUnit 测试
REM 编译原理实验：后缀表达式 Postfix

REM 切换到项目根目录
cd /d "%~dp0.."

echo ========================================
echo   运行 JUnit 单元测试
echo ========================================
echo.

REM 检查 JUnit 库是否存在
if not exist lib\junit-4.13.2.jar (
    echo 错误: 未找到 lib\junit-4.13.2.jar
    echo 请先下载 JUnit 库到 lib 目录
    echo 参考 lib\README.md 获取下载说明
    pause
    exit /b 1
)

if not exist lib\hamcrest-core-1.3.jar (
    echo 错误: 未找到 lib\hamcrest-core-1.3.jar
    echo 请先下载 Hamcrest 库到 lib 目录
    echo 参考 lib\README.md 获取下载说明
    pause
    exit /b 1
)

REM 检查编译后的类是否存在
if not exist bin\ParserTest.class (
    echo 正在编译测试类...
    call scripts\build.bat
)

echo 运行测试...
echo.

java -cp "bin;lib\junit-4.13.2.jar;lib\hamcrest-core-1.3.jar" org.junit.runner.JUnitCore ParserTest

echo.
echo ========================================
echo   测试完成
echo ========================================
pause