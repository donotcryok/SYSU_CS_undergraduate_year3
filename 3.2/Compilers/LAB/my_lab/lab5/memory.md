# 工作记录 (Memory)

## 实验一：熟悉 Oberon-0 语言定义

| 时间 | 内容 |
|------|------|
| 2026-06-18 | 初始化项目结构，创建 memory.md / todo.md |
| 2026-06-18 | 完成任务一：`ex1/testcases/StudentStats.obr` 全覆盖 Oberon-0 源程序 |
| 2026-06-18 | 完成任务二：8 个变异测试片段 → `ex1/testcases/` |
| 2026-06-18 | 完成任务三：保留字 vs 关键字 + 悬挂 else 理论解答 |
| 2026-06-18 | 修复 ROSE 工具集 JDK 9+ Module 冲突 |
| 2026-06-18 | 填充 `ex1/Oberon-0.tex` 完整实验报告 |

## 实验二：自动生成词法分析器 (JFlex)

| 时间 | 内容 |
|------|------|
| 2026-06-18 | 创建 ex2 完整目录结构 + 5 个异常类 |
| 2026-06-18 | 编写 `ex2/src/oberon.flex` (OberonScanner, %ignorecase, 5 种异常检测) |
| 2026-06-18 | 编写 4 个 bat 脚本 (gen → build → run → test 流程) |
| 2026-06-18 | 填充 `ex2/lexgen.tex` 实验报告（词汇表/正则/JFlex对比/心得） |
| 2026-06-18 | 修复 JFLEX_HOME 硬编码 → gen.bat 直接 java -jar |
| 2026-06-18 | 创建自包含 Token.java (58 常量)，去除 CUP 依赖 |
| 2026-06-18 | gen.bat + build.bat 成功，StudentStats.obr 扫描得 568 tokens |
| 2026-06-18 | 插入 10 张截图到 lexgen.tex |

## 实验三：自动生成语法分析器 (JavaCUP + CallGraph)

| 时间 | 内容 |
|------|------|
| 2026-06-18 | 从 ex2 拷贝 OberonScanner.java/Token.java/exceptions 到 ex3/src/ |
| 2026-06-18 | 创建 ex3 目录结构 + 4 支批处理脚本 |
| 2026-06-18 | 编写 `ex3/src/oberon.cup` (87条产生式, LALR(1), 0冲突) |
| 2026-06-18 | 编写 `ex3/src/CupScanner.java` (Token→sym 映射, HashMap 49对) |
| 2026-06-18 | 编写 `ex3/src/OberonParserTest.java` (CallGraph + Parser 测试驱动) |
| 2026-06-18 | 编写 `ex3/yaccgen.tex` (JavaCUP vs Bison, JavaCC vs JavaCUP 对比) |
| 2026-06-18 | 修复 JavaCUP 问题: EOF 重复声明 → 移除; UMINUS 未声明 → 移除 %prec |
| 2026-06-18 | 修复 reduce-reduce 冲突: statement ::= /* empty */ 移除 |
| 2026-06-18 | 修复 Token→sym 映射: JavaCUP 重新编号, CupScanner 显式映射 |
| 2026-06-18 | 修复分号处理: const_decl/type_decl/var_decl 将 SEMI 纳入产生式 |
| 2026-06-18 | gen.bat + build.bat 成功, StudentStats.obr 语法分析通过 |
| 2026-06-18 | CallGraph 输出: 6 过程, 6 调用点, 6 边 |
| 2026-06-19 | 按 ex2/lexgen.tex 模板重写 yaccgen.tex |
| 2026-06-19 | 插入 4 张截图 (gen_ok / build_ok / parse_ok1 / parse_ok2) |
| 2026-06-19 | 终结符编码对照表拆分为 2 个子表 (保留字21行 + 运算符分界符28行) |

## 实验四：手工编写递归下降分析程序 (Flowchart)

| 时间 | 内容 |
|------|------|
| 2026-06-19 | 创建 ex4 完整目录结构 |
| 2026-06-19 | 从 ex2 拷贝 OberonScanner/Token/exceptions 到 ex4/src/ |
| 2026-06-19 | 编写 3 支批处理脚本 (build/run/test) |
| 2026-06-19 | 编写 `ex4/src/OberonParser.java` |
|        | - parseModule() → module = new FlowchartModule() |
|        | - parseProcedureDeclaration() → proc = module.add(name) |
|        | - parseStatementSequence(target) → target.add(stmt) |
|        | - parseIfStatement() → IfStatement(cond) + True/False 分支 |
|        | - parseWhileStatement() → WhileStatement(cond) + 循环体 |
|        | - parseExpression() → parseSimpleExpr → parseTerm → parseFactor (优先级分层) |
|        | - 用 while 循环消除 EBNF 闭包中的左递归 |
|        | - 继承属性: 方法参数传递 target 容器 |
|        | - 综合属性: 返回值传递表达式字符串 / 语句节点 |
| 2026-06-19 | 编写 `ex4/src/OberonParserTest.java` (FileReader + module.show()) |
| 2026-06-19 | 编写 `ex4/scheme.tex` 实验报告 |
|        | - LL(1) 改造策略 + 左递归消除 |
|        | - 翻译模式伪代码 (含语义动作标注) |
|        | - 继承属性与综合属性传递机制 |
|        | - LL vs LR 深度对比 (10 维度) |
| 2026-06-19 | 更新 todo.md + memory.md |

### 关键决策

1. **左递归消除**：利用 EBNF 闭包 `{...}` 天然的非递归特性，在递归下降中用 while 循环直接转换，
   无需显式改写文法为右递归。

2. **属性传递**：继承属性通过方法参数（如 parseStatementSequence 的 target 参数），
   综合属性通过返回值（如 parseExpression 返回字符串）。与 LALR 的全局栈方案形成清晰对比。

3. **Flowchart API 节点创建时机**：在语句解析方法入口创建（如 parseWhileStatement
   开头 new WhileStatement），保证流程图结构与语法分析同步推进。

4. **ELSIF 模拟**：Flowchart API 无原生 ELSIF 节点，使用嵌套 IfStatement
   挂在上一级 If 的 false 分支中模拟链式条件。
