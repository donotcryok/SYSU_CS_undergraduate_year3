# 人工待办清单 (TODO)

## 实验一：熟悉 Oberon-0 语言定义 ✅ 全部完成

## 实验二：自动生成词法分析器 (JFlex) ✅ 全部完成

## 实验三：自动生成语法分析器 (JavaCUP + CallGraph) ✅ 全部完成

## 实验四：手工编写递归下降分析程序 (Flowchart)

### 自动化已完成 ✅
- [x] 创建 ex4 目录树 (src/, bin/, doc/, src/exceptions/)
- [x] 从 ex2 拷贝 OberonScanner.java / Token.java / exceptions/
- [x] 编写 3 个批处理脚本 (build.bat / run.bat / test.bat)
- [x] 创建 `ex4/readme.txt` 自述文件
- [x] 编写递归下降核心 `ex4/src/OberonParser.java`
  - [x] parseModule() → parseDeclarationSequence() → parseStatementSequence()
  - [x] parseIfStatement() / parseWhileStatement() / parseExpression()
  - [x] 表达式优先级分层: parseExpression → parseSimpleExpr → parseTerm → parseFactor
  - [x] Flowchart API 集成: Module.add() → Procedure.add() → IfStatement / WhileStatement / PrimitiveStatement
- [x] 编写测试驱动 `ex4/src/OberonParserTest.java`
- [x] 填充 `ex4/scheme.tex` 实验报告 (LL(1) 改造 + 翻译模式 + LL vs LR 对比)

### 人工待完成
- [ ] 拷贝 flowchart API 包 (LabInstrument05-ROSE/lib/flowchart.jar + jgraph.jar) —— 已就位
- [ ] 运行 `ex4/build.bat` 编译
- [ ] 运行 `ex4/run.bat ..\ex1\testcases\StudentStats.obr` 测试
- [ ] 截图保存至 `ex4/img/` (build_ok.png + parse_ok.png)
- [ ] 编译 `ex4/scheme.tex` 生成 PDF
- [ ] 手工联调修补 Parser 的边角逻辑 (LL(1) 冲突、恐慌恢复等)
