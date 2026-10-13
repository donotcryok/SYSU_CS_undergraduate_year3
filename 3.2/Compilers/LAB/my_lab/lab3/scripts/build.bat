@echo off
REM 编译脚本 - 编译所有 Java 源文件
REM 编译原理实验：后缀表达式 Postfix

REM 切换到项目根目录
cd /d "%~dp0.."

echo ========================================
echo   编译 Postfix 项目
echo ========================================
echo.

REM 创建 bin 目录（如果不存在）
if not exist bin mkdir bin

REM 编译主程序
echo 正在编译主程序...
javac -encoding UTF-8 -d bin src\Postfix.java
if %errorlevel% neq 0 (
    echo 编译主程序失败！
    pause
    exit /b 1
)
echo 主程序编译成功！

REM 编译性能测试类
echo 正在编译性能测试类...
javac -encoding UTF-8 -cp bin -d bin src\PerformanceTest.java
if %errorlevel% neq 0 (
    echo 编译性能测试类失败！
    pause
    exit /b 1
)
echo 性能测试类编译成功！

REM 检查 JUnit 库是否存在
if exist lib\junit-4.13.2.jar (
    if exist lib\hamcrest-core-1.3.jar (
        echo 正在编译单元测试类...
        javac -encoding UTF-8 -cp "bin;lib\junit-4.13.2.jar;lib\hamcrest-core-1.3.jar" -d bin src\ParserTest.java
        if %errorlevel% neq 0 (
            echo 编译单元测试类失败！
            pause
            exit /b 1
        )
        echo 单元测试类编译成功！
    ) else (
        echo 警告: 未找到 lib\hamcrest-core-1.3.jar，跳过单元测试编译
    )
) else (
    echo 警告: 未找到 lib\junit-4.13.2.jar，跳过单元测试编译
    echo 如需运行单元测试，请下载 JUnit 库到 lib 目录
)

echo.
echo ========================================
echo   编译完成！
echo ========================================
echo.
echo 可执行命令:
echo   scripts\run.bat       - 运行主程序
echo   scripts\test.bat      - 运行单元测试
echo   scripts\perf_test.bat - 运行性能测试
echo.
pause