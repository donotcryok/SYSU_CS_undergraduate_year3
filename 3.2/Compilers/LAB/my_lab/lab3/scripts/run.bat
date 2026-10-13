@echo off
REM 运行脚本 - 运行主程序
REM 编译原理实验：后缀表达式 Postfix

REM 切换到项目根目录
cd /d "%~dp0.."

cd bin
java Postfix
cd ..
pause
@echo on