@echo off
:: 切换到项目根目录
cd /d "%~dp0.."

echo [*] 正在编译源码...
javac -encoding UTF-8 src\*.java

echo [*] 正在生成 Javadoc 文档...
javadoc -d doc -encoding UTF-8 -charset UTF-8 -quiet src\*.java

echo [*] 构建完成，请查看 doc 文件夹。
pause