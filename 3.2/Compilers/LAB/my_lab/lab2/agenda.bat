@echo off
REM ===========================================================
REM     Agenda 议程管理系统 - 运行脚本
REM ===========================================================
REM 
REM 作者: 马福泉
REM 学号: 23336179
REM 
REM 功能: 运行 Agenda 系统
REM

echo 正在启动 Agenda 系统...
echo.

REM 检查编译文件是否存在
if not exist "bin\AgendaService.class" (
    echo 错误: 未找到编译文件！
    echo 请先运行 build.bat 进行编译。
    echo.
    pause
    exit /b 1
)

REM 运行程序
java -cp bin AgendaService

pause