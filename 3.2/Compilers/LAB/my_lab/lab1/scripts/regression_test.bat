@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0.."
title 回归测试工具

echo [*] 开始执行自动化回归测试...

:: 强制结束残留进程并编译
taskkill /F /IM java.exe >nul 2>&1
javac -encoding UTF-8 src\*.java

:: 设置日志文件路径
set LOG=test_cases\test_report.log
echo 测试时间: %date% %time% > "%LOG%"

:: 遍历用例并追加输出
for %%f in (test_cases\*.txt) do (
    echo [运行中] %%f
    echo. >> "%LOG%"
    echo ########## 用例: %%f ########## >> "%LOG%"
    
    :: 运行并重定向输出流
    java -cp src TaxApp < "%%f" >> "%LOG%" 2>&1
)

echo [*] 测试全部完成！