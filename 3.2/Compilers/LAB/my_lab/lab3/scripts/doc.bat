@echo off
REM 文档生成脚本 - 生成 Javadoc API 文档
REM 编译原理实验：后缀表达式 Postfix

REM 切换到项目根目录
cd /d "%~dp0.."

echo ========================================
echo   生成 Javadoc API 文档
echo ========================================
echo.

javadoc -d doc -private src\Postfix.java

echo.
echo ========================================
echo   文档生成完成
echo ========================================
echo.
echo 文档位置: doc/index.html
echo.
pause