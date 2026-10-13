@echo off
echo ========================================
echo   ROSE 实验二 —— 生成 Javadoc 文档
echo ========================================
echo.

REM 实验二无外部 jar 依赖，直接生成
REM 使用显式源文件列表，避免 -subpackages . 爬取外部目录
javadoc -d doc -sourcepath src src\*.java src\exceptions\*.java -encoding UTF-8 -charset UTF-8 -author -version

echo.
echo Javadoc 生成完毕，已存入 doc 目录。
pause
