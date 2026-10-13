@echo off
REM 测试用例 004 - 缺少运算量测试
REM 编译原理实验：后缀表达式 Postfix

REM 切换到项目根目录
cd /d "%~dp0.."

@echo Running Testcase 004: missing an operand.
@echo ==============================================
@echo The input is:
type testcases\tc-004.infix
@echo ----------------------------------------------
cd bin

rem : Run the testcase with input direction
java Postfix < ..\testcases\tc-004.infix

rem : Compare the expected output
@echo ----------------------------------------------
@echo The output should be: 
type ..\testcases\tc-004.postfix

cd ..
@echo ==============================================
pause
@echo on