============================================================
 ROSE —— 编译原理逆向工程工具
 Lab3: 自动生成语法分析程序 (JavaCUP)
============================================================

姓    名: （已隐藏）
学    号: 23336179
邮    箱: （已隐藏）
完成日期: 2026 年 6 月

补充说明:
本目录包含实验三自动生成的 JavaCUP 语法分析器及测试脚本。
语法分析过程集成了调用图 (CallGraph) 的生成逻辑。

快速开始:
  1. java-cup-11b.jar 和 java-cup-11b-runtime.jar 已放入 Javacup/
  2. 将 ex2/src/OberonScanner.java 和 ex2/src/Token.java 拷贝到 ex3/src/
  3. 将 ex2/src/exceptions/ 目录拷贝到 ex3/src/exceptions/
  4. 双击 gen.bat 生成 Parser.java + Symbol.java
  5. 双击 build.bat 编译所有 Java 文件
  6. 双击 run.bat ..\ex1\testcases\StudentStats.obr 运行语法分析

目录结构:
  ex3/
  ├── readme.txt                    本文件
  ├── yaccgen.pdf                   实验三报告
  ├── gen.bat                       JavaCUP 代码生成脚本
  ├── build.bat                     Java 编译脚本
  ├── run.bat                       运行脚本
  ├── test.bat                      批量测试脚本
  ├── Javacup/
  │   ├── java-cup-11b.jar           JavaCUP 生成器
  │   └── java-cup-11b-runtime.jar   JavaCUP 运行时
  ├── src/
  │   ├── oberon.cup                 JavaCUP 语法规则文件
  │   ├── Symbol.java               [生成] 符号常量
  │   ├── Parser.java               [生成] LALR 语法分析器
  │   ├── OberonScanner.java        [从 ex2 拷贝] 词法分析器
  │   ├── Token.java                [从 ex2 拷贝] Token 类
  │   └── exceptions/               [从 ex2 拷贝] 异常类
  ├── bin/                          编译产物
  └── doc/                          文档
