@echo off
REM ===========================================================
REM     Agenda 议程管理系统 - 编译脚本
REM ===========================================================
REM 
REM 作者: 马福泉
REM 学号: 23336179
REM 
REM 功能: 编译所有 Java 源代码文件
REM

echo 正在编译 Agenda 系统...
echo.

REM 创建输出目录（如果不存在）
if not exist "bin" mkdir bin

REM 清理旧的编译文件
if exist "bin\*" del /q /s "bin\*" 2>nul

REM 编译所有 Java 文件
echo 编译 src 目录下的所有 Java 文件...
javac -encoding UTF-8 -d bin -sourcepath src src\agenda\entity\*.java src\agenda\exception\*.java src\agenda\storage\*.java src\agenda\service\*.java src\agenda\ui\*.java src\AgendaService.java

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo 编译失败！请检查错误信息。
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo 编译成功！
echo 输出目录: bin
echo ========================================
echo.

REM 生成 Javadoc 文档
echo 正在生成 Javadoc 文档...
if not exist "doc" mkdir doc
javadoc -encoding UTF-8 -charset UTF-8 -d doc -sourcepath src -subpackages agenda src\AgendaService.java

if %errorlevel% neq 0 (
    echo Javadoc 生成失败，但编译已成功。
)

echo.
echo 编译和文档生成完成！
echo 运行程序请执行: agenda.bat
echo.

pause