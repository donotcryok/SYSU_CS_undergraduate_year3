@echo off
REM ============================================
REM test.bat —— 运行测试用例
REM 用法: test.bat [测试用例路径]
REM ============================================
if "%~1"=="" (
    echo 用法: test.bat ^<测试用例路径^>
    echo 示例: test.bat ..\ex1\testcases\mut1_IllegalSymbol.obr
    pause
    exit /b 1
)
echo [test] 正在测试: %1
java -cp bin;Javacup\java-cup-11b-runtime.jar;..\LabInstrument05-ROSE\lib\callgraph.jar;..\LabInstrument05-ROSE\lib\jgraph.jar OberonParserTest %1
pause
