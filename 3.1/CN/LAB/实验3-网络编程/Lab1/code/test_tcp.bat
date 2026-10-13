@echo off
echo ===============================================
echo           TCP通信实验测试脚本
echo ===============================================
echo.
echo 本脚本用于快速测试TCP通信程序
echo.
echo 使用说明:
echo 1. 首先在一个命令窗口运行此脚本选择1启动服务器
echo 2. 然后在另一个命令窗口运行此脚本选择2启动客户端  
echo 3. 可以打开多个客户端窗口进行多用户聊天测试
echo 4. 在进行测试前请先启动Wireshark监控网络数据包
echo.
echo ===============================================
echo.

:menu
echo 请选择要执行的操作:
echo 1. 启动TCP服务器
echo 2. 启动TCP客户端 
echo 3. 编译程序
echo 4. 查看程序文件
echo 5. 退出
echo.
set /p choice=请输入选择 (1-5): 

if "%choice%"=="1" goto server
if "%choice%"=="2" goto client
if "%choice%"=="3" goto compile
if "%choice%"=="4" goto list
if "%choice%"=="5" goto exit
echo 无效选择，请重新输入
goto menu

:server
echo.
echo 启动TCP服务器...
echo 提示: 现在可以启动Wireshark监控端口8889的TCP流量
echo.
extend.exe
goto menu

:client  
echo.
echo 启动TCP客户端...
echo 提示: 请确保服务器已经启动
echo.
extend.exe
goto menu

:compile
echo.
echo 编译TCP通信程序...
gcc -o extend.exe extend.c -lws2_32
if %errorlevel%==0 (
    echo 编译成功！
) else (
    echo 编译失败，请检查代码！
)
echo.
pause
goto menu

:list
echo.
echo 程序文件列表:
dir *.c *.exe
echo.
pause
goto menu

:exit
echo.
echo 程序退出
exit