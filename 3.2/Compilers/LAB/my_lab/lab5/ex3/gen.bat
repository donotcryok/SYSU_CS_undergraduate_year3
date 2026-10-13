@echo off
REM ============================================
REM gen.bat —— 调用 JavaCUP 从 oberon.cup 生成 Parser.java + Symbol.java
REM 前提: Javacup/java-cup-11b.jar 已就位
REM ============================================
echo [gen] 正在调用 JavaCUP 生成语法分析器 ...
java -jar Javacup\java-cup-11b.jar -destdir src -parser Parser -symbols sym src\oberon.cup
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [gen] JavaCUP 生成失败，请检查 oberon.cup 语法。
    pause
    exit /b 1
)
echo.
echo [gen] Parser.java 和 Symbol.java 已生成至 src/ 目录。
echo [gen] 下一步: 运行 build.bat 编译。
pause
