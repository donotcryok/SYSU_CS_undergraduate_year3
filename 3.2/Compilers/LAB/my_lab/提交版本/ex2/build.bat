@echo off
REM ============================================
REM build.bat —— 编译所有 Java 源文件到 bin/
REM ============================================
echo [build] 正在编译 Java 源文件 ...

REM 编译 Token.java (无包声明, 在 src/ 根下)
javac -d bin src\Token.java
if %ERRORLEVEL% NEQ 0 (
    echo [build] Token.java 编译失败。
    pause
    exit /b 1
)

REM 编译异常类 (package exceptions; sourcepath 指向 src/)
javac -d bin -sourcepath src src\exceptions\*.java
if %ERRORLEVEL% NEQ 0 (
    echo [build] exceptions 编译失败。
    pause
    exit /b 1
)

REM 编译 OberonScanner (无包声明, 依赖 Token 和 exceptions)
javac -d bin -classpath bin -sourcepath src src\OberonScanner.java
if %ERRORLEVEL% NEQ 0 (
    echo [build] OberonScanner.java 编译失败，请检查错误信息。
    pause
    exit /b 1
)

echo [build] 编译成功，class 文件已输出至 bin/ 目录。
pause
