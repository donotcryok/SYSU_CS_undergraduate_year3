@echo off
REM ============================================
REM build.bat —— 编译实验四递归下降解析器
REM 依赖: flowchart.jar + jgraph.jar
REM        OberonScanner.java / Token.java / exceptions/ 已拷贝到 src/
REM ============================================
echo [build] 正在编译实验四 Java 源文件 ...
javac -cp ..\LabInstrument05-ROSE\lib\flowchart.jar;..\LabInstrument05-ROSE\lib\jgraph.jar;src -d bin src\OberonParser.java src\OberonParserTest.java src\*.java src\exceptions\*.java
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [build] 编译失败，请检查错误信息。
    echo   常见原因:
    echo   1. OberonScanner.java / Token.java 未拷贝到 ex4/src/
    echo   2. flowchart.jar / jgraph.jar 路径不正确
    pause
    exit /b 1
)
echo [build] 编译成功，class 文件已输出至 bin/ 目录。
pause
