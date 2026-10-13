============================================================
 ROSE —— 编译原理逆向工程工具
 Lab4: 手工编写递归下降语法分析程序 (含流程图生成)
============================================================

姓    名: （已隐藏）
学    号: 23336179
邮    箱: （已隐藏）
完成日期: 2026 年 6 月 19 日

补充说明:
本目录包含实验四手工编写的 Oberon-0 递归下降语法分析器及测试脚本。
解析器在执行语法制导翻译时集成了流程图 (Flowchart) 的自动生成 API。

快速开始:
  1. 将 ex2/src/OberonScanner.java、Token.java 拷贝到 ex4/src/
  2. 将 ex2/src/exceptions/ 拷贝到 ex4/src/exceptions/
  3. 双击 build.bat 编译所有 Java 文件
  4. 双击 run.bat ..\ex1\testcases\StudentStats.obr 运行语法分析并显示流程图

目录结构:
  ex4/
  ├── readme.txt                    本文件
  ├── scheme.pdf                    实验四报告
  ├── build.bat                     Java 编译脚本
  ├── run.bat                       运行脚本
  ├── test.bat                      测试脚本
  ├── src/
  │   ├── OberonParser.java         递归下降语法分析器 (核心)
  │   ├── OberonParserTest.java     测试驱动
  │   ├── OberonScanner.java        [从 ex2 拷贝] 词法分析器
  │   ├── Token.java                [从 ex2 拷贝] Token 类
  │   └── exceptions/               [从 ex2 拷贝] 异常类
  ├── bin/                          编译产物
  └── doc/                          文档
