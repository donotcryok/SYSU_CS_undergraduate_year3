@echo off
cd ..\src
javadoc -private -author -version -encoding UTF-8 -d ..\doc -classpath ..\bin parser\*.java
cd ..
pause
@echo on
