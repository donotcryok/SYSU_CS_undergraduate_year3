@echo off
cd ..\bin
java test.ExprEvalTest ..\testcases\mytest.xml  > ..\testcases\report_mytest.txt
cd ..
type testcases\report_mytest.txt
pause
del testcases\report_mytest.txt
@echo on
