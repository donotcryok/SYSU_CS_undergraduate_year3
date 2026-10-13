@echo off
REM 测试用例运行脚本 - 运行所有测试用例
REM 编译原理实验：后缀表达式 Postfix

REM 切换到项目根目录
cd /d "%~dp0.."

call scripts\testcase-001.bat
call scripts\testcase-002.bat
call scripts\testcase-003.bat
call scripts\testcase-004.bat
@echo on