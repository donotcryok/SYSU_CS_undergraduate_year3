@echo off
cd /d "%~dp0.."

echo [*] 正在清理生成的 .class 文件...

del /s /q src\*.class

echo [*] 清理完毕！。
pause