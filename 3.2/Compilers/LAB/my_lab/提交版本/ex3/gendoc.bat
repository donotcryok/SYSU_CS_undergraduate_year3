@echo off
echo ========================================
echo   ROSE 实验三 —— 生成 Javadoc 文档
echo ========================================
echo.

REM 实验三依赖: java-cup-11b-runtime.jar, callgraph.jar, jgraph.jar
set CP=Javacup\java-cup-11b-runtime.jar;..\LabInstrument05-ROSE\lib\callgraph.jar;..\LabInstrument05-ROSE\lib\jgraph.jar

REM 使用显式源文件列表，避免 -subpackages . 爬取外部目录
javadoc -d doc -sourcepath src src\*.java src\exceptions\*.java -classpath "%CP%" -encoding UTF-8 -charset UTF-8 -author -version

echo.
echo Javadoc 生成完毕，已存入 doc 目录。
pause
