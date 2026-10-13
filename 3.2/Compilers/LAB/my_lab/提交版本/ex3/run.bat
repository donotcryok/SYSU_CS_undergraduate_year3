@echo off
REM ============================================
REM run.bat —— 运行语法分析器解析指定 Oberon-0 源文件
REM 用法: run.bat [Oberon源文件]
REM ============================================
if "%~1"=="" (
    echo 用法: run.bat ^<Oberon-0源文件路径^>
    echo 示例: run.bat ..\ex1\testcases\StudentStats.obr
    pause
    exit /b 1
)
echo [run] 正在解析: %1
java -cp bin;Javacup\java-cup-11b-runtime.jar;..\LabInstrument05-ROSE\lib\callgraph.jar;..\LabInstrument05-ROSE\lib\jgraph.jar OberonParserTest %1
pause
