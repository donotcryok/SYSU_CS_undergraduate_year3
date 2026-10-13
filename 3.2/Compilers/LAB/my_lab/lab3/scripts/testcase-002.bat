@echo off
REM 测试用例 002 - 正确长输入测试
REM 编译原理实验：后缀表达式 Postfix

REM 切换到项目根目录
cd /d "%~dp0.."

@echo Running Testcase 002: a correct long input.
@echo ==============================================
@echo The input is:
type testcases\tc-002.infix
@echo ----------------------------------------------
cd bin

rem : Run the testcase with input direction
java Postfix < ..\testcases\tc-002.infix

rem : Compare the expected output
@echo ----------------------------------------------
@echo The output should be: 
type ..\testcases\tc-002.postfix

cd ..
@echo ==============================================
pause
@echo on