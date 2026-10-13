@echo off
cd ..\src
javac -encoding UTF-8 -d ..\bin -classpath ..\bin exceptions\*.java parser\*.java gui\*.java ExprEval.java
cd ..
pause
@echo on
