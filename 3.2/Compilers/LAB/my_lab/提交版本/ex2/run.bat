@echo off
REM ============================================
REM run.bat —— 运行词法分析器扫描指定源文件
REM 用法: run.bat [Oberon源文件]
REM ============================================
if "%~1"=="" (
    echo 用法: run.bat ^<Oberon-0源文件路径^>
    echo 示例: run.bat ..\ex1\testcases\StudentStats.obr
    pause
    exit /b 1
)
echo [run] 正在扫描: %1
java -classpath bin OberonScannerTest %1
pause
