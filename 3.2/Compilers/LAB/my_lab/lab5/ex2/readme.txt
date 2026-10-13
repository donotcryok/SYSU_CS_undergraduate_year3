============================================================
 ROSE —— 编译原理逆向工程工具
 Lab2: 自动生成词法分析程序 (JFlex)
============================================================

姓    名: （已隐藏）
学    号: 23336179
邮    箱: （已隐藏）
完成日期: 2026 年 6 月 18 日

  1. 从 https://jflex.de/ 下载 JFlex 工具包
  2. 将解压后的 jflex 文件夹放入 ex2/jflex/ (确保 jflex/bin/jflex.bat 存在)
  3. 双击 gen.bat 生成 OberonScanner.java
  4. 双击 build.bat 编译所有 Java 文件
  5. 双击 run.bat ..\ex1\testcases\StudentStats.obr 扫描示例程序

目录结构:
  ex2/
  ├── readme.txt                  本文件
  ├── lexgen.pdf                  实验二报告
  ├── gen.bat                     JFlex 代码生成脚本
  ├── build.bat                   Java 编译脚本
  ├── run.bat                     运行脚本 (扫描单个 .obr)
  ├── test.bat                    批量测试脚本
  ├── jflex/                      [须自行放入] JFlex 工具包
  ├── src/
  │   ├── oberon.flex              JFlex 词法规则定义文件
  │   └── exceptions/              自定义异常类 (5 种)
  ├── bin/                        编译产物
  └── doc/                        文档
