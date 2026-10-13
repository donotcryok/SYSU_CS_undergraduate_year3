@echo off
REM ============================================
REM gen.bat —— 调用 JFlex 从 oberon.flex 生成 OberonScanner.java
REM 前提: jflex/ 目录已包含 JFlex 完整工具包
REM ============================================

REM 设置 JFLEX_HOME 为当前目录下的 jflex 子目录
set JFLEX_HOME=%~dp0jflex
set JFLEX_VERSION=1.9.1

echo [gen] JFLEX_HOME=%JFLEX_HOME%
echo [gen] 正在调用 JFlex 生成词法分析器 ...

java -Xmx128m -jar "%JFLEX_HOME%\lib\jflex-full-%JFLEX_VERSION%.jar" -d src src\oberon.flex

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [gen] JFlex 生成失败。常见原因：
    echo   1. jflex\lib\jflex-full-1.9.1.jar 不存在
    echo   2. src\oberon.flex 语法有误
    echo   3. 请检查上方的具体错误信息
    pause
    exit /b 1
)
echo.
echo [gen] OberonScanner.java 已生成至 src/ 目录。
echo [gen] 下一步: 运行 build.bat 编译。
pause
