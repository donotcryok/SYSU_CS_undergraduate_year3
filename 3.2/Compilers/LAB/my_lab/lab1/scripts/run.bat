@echo off
cd /d "%~dp0.."

echo [*] 正在编译源码...
javac -encoding UTF-8 src\*.java

if %errorlevel% neq 0 (
    echo [!] 编译失败！
    pause
    exit /b
)

echo [*] 启动个人所得税计算器...
echo ---------------------------------------
:: 使用 -cp src 指定类路径
java -cp src TaxApp

echo ---------------------------------------
pause