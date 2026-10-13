@echo off
REM ============================================
REM build.bat —— 编译所有 Java 源文件到 bin/
REM 依赖: gen.bat 已运行(生成 Parser.java+Symbol.java)
REM        ex2 的 OberonScanner/Token/exceptions 已拷贝到 src/
REM ============================================
echo [build] 正在编译 Java 源文件 ...

REM 编译所有源文件 (runtime jar + callgraph + jgraph)
javac -cp Javacup\java-cup-11b-runtime.jar;..\LabInstrument05-ROSE\lib\callgraph.jar;..\LabInstrument05-ROSE\lib\jgraph.jar;src -d bin src\*.java src\exceptions\*.java
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [build] 编译失败，请检查错误信息。
    echo   常见原因:
    echo   1. 未运行 gen.bat 生成 Parser.java 和 Symbol.java
    echo   2. 未从 ex2 拷贝 OberonScanner.java / Token.java / exceptions/
    echo   3. classpath 中 jar 包路径不正确
    pause
    exit /b 1
)
echo [build] 编译成功，class 文件已输出至 bin/ 目录。
pause
