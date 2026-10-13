============================================================
 ROSE —— 编译原理逆向工程工具
 Lab1: 熟悉 Oberon-0 语言定义
============================================================

姓    名: （已隐藏）
学    号: 23336179
专    业: 计算机科学与技术
电子邮件: （已隐藏）
联系电话: （已隐藏）
完成日期: 2026 年 6 月 18 日

============================================================
 目录结构说明
============================================================

ex1/
├── readme.txt                   本文件
├── Oberon-0.pdf                已编译的 PDF 报告
├── testcases/
│   ├── StudentStats.obr        任务一：全覆盖 Oberon-0 正确源程序
├── img/
│   ├── SYSULogo.png           校徽
│   ├── error.png               ROSE 编译失败截图 (JDK 9+ 冲突)
│   └── flowchartDemoAccount.png ROSE 流程图运行截图
└── testcases/
    ├── mut1_IllegalSymbol.obr       词法错误：非法符号 @
    ├── mut2_IllegalInteger.obr      词法错误：数字与标识符粘连
    ├── mut3_IllegalOctal.obr        词法错误：非法八进制
    ├── mut4_MismatchedComment.obr   词法错误：注释不闭合
    ├── mut5_MissingParenthesis.obr  语法错误：缺括号
    ├── mut6_MissingOperator.obr     语法错误：缺运算符
    ├── mut7_TypeMismatched.obr      语义错误：类型不兼容
    └── mut8_ParameterMismatched.obr 语义错误：参数数目不匹配

============================================================
 补充说明
============================================================

1. ROSE 工具链在本环境中运行时遇到 JDK 9+ 引入的 java.lang.Module
   与 flowchart.jar 中 flowchart.Module 的命名冲突，已通过将三个
   Demo 源文件中的 Module 改为完全限定名 flowchart.Module 修复。

2. 编译环境: JDK 17, Windows 11, PowerShell; LaTeX: pdfLaTeX + ctex。

3. Oberon-0.tex 中的所有路径均为相对于 ex1/ 的相对路径，在图 1/图 2
   中引用 img/error.png 和 img/flowchartDemoAccount.png。

4. 实验报告中的理论分析涵盖: 保留字 vs 预定义标识符的编译器实现差异、
   表达式强类型系统对比、悬挂 else 二义性的 fully-bracketed 消除方案。

