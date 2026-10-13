# Memory Bank - 编译原理实验：后缀表达式 Postfix

## 项目状态

**当前阶段**: 项目最终收尾完成，准备打包提交  
**完成日期**: 2026年4月27日  
**项目版本**: 3.0 (工程化重构版)

---

## ✅ 已完成的工作

### 第一阶段：核心代码重构与功能扩展

#### Step 1: 静态与非静态重构 ✅
- **修改内容**: 将 `Parser` 类中的 `static int lookahead` 改为 `private int lookahead`
- **新增成员**: 
  - `private int position` - 用于错误定位的位置索引
  - `private PushbackReader reader` - 输入流读取器
  - `private List<CompileError> errors` - 错误收集列表
- **优势**: 
  - 支持多实例隔离
  - 线程安全
  - 符合面向对象封装原则

#### Step 2: 消除尾递归 ✅
- **原始实现**: 递归版本的 `rest()` 方法
- **重构实现**: 使用 `while (lookahead == '+' || lookahead == '-')` 循环
- **优势**:
  - 避免栈溢出风险
  - 提高执行效率
  - 支持超长表达式解析

#### Step 3: 扩展错误处理与恢复 ✅
- **错误分类**: 
  - `LEXICAL_ERROR` - 词法错误（空白符、非法字符）
  - `SYNTAX_ERROR` - 语法错误（缺少运算量、连续运算符）
- **错误定位**: 
  - 记录错误发生的位置索引
  - 记录引起错误的字符
- **Panic-Mode 恢复**: 
  - 同步记号集合: `"0123456789+-"`
  - `skipInvalidTokens()` 方法实现跳过非法字符
  - 支持一次运行报告多个错误

#### Step 4: Javadoc 注释 ✅
- 为所有类、方法添加标准 Javadoc 注释
- 包含 `@param`, `@return`, `@throws` 等标签
- 详细说明方法的功能和实现原理

#### Step 5: JUnit 单元测试 ✅
- **测试类**: `ParserTest.java`
- **测试覆盖**:
  - 正常表达式转换（单数字、简单加减、多运算符）
  - 词法错误检测（空格、制表符、非法字符）
  - 语法错误检测（缺少运算量、连续运算符）
  - 错误定位验证
  - Panic-Mode 恢复验证
- **测试结果**: 21个测试全部通过

---

### 第二阶段：性能测试脚本设计 ✅

#### PerformanceTest.java (v2.1 - 数据持久化版本)
- **功能**: 
  - 自动生成不同长度的合法中缀表达式
  - 对比递归版本与循环版本的执行时间
  - 自动保存结果到 `data/perf_results.csv`
- **测试长度**: 100, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000
- **测试次数**: 每个长度测试5次取平均值
- **输出指标**: 
  - 执行时间（毫秒）
  - 最大栈深度
  - 加速比
  - 栈溢出标记（NaN）

#### 测试结果数据
```
ExpressionLength,RecursiveTime_ms,IterativeTime_ms,StackDepth,Speedup
100,0,0,50,0.00
500,0,0,250,0.00
1000,0,0,500,0.00
2000,0,0,1000,0.00
5000,1,1,2500,1.00
10000,3,3,5000,1.00
20000,NaN,0,0,NaN    ← 递归版本栈溢出
50000,NaN,18,0,NaN
100000,NaN,11,0,NaN
```

---

### 第三阶段：Python 可视化脚本 ✅

#### scripts/plot_perf.py
- **功能**: 读取 CSV 数据，生成性能对比折线图
- **特性**:
  - 使用 pandas 读取 CSV 数据
  - 使用 matplotlib 绘制双折线图
  - 标注栈溢出临界点（红色竖线）
  - 中文字体支持（SimHei）
- **输出**: `img/performance_chart.png` (183KB)

---

### 第四阶段：实验报告撰写 ✅

#### design.tex 更新内容
- 项目结构说明（含 scripts/ 目录整合说明）
- 性能测试结果表格（已填写实际数据）
- 性能对比图表插入
- 错误处理截图插入（词法、语法、Panic-Mode）
- JUnit 测试结果截图插入
- 个人信息填写完成

---

### 第五阶段：工程化重构 ✅ (2026年4月27日)

#### 脚本目录整合
- **操作**: 将所有 `.bat` 脚本从根目录移动到 `scripts/` 目录
- **移动文件**:
  - `build.bat` → `scripts/build.bat`
  - `run.bat` → `scripts/run.bat`
  - `test.bat` → `scripts/test.bat`
  - `perf_test.bat` → `scripts/perf_test.bat`
  - `doc.bat` → `scripts/doc.bat`
  - `testcase.bat` → `scripts/testcase.bat`
  - `testcase-001~004.bat` → `scripts/testcase-001~004.bat`
- **路径修复**: 所有脚本添加 `cd /d "%~dp0.."` 切换到项目根目录
- **目的**: 保持根目录整洁，符合现代工程规范

#### 文档同步更新
- **readme.txt**: 更新目录结构树和使用说明
- **design.tex**: 添加项目结构说明表格和脚本说明表格
- **TODO.md**: 标记所有任务完成，添加提交前检查清单
- **memory_bank.md**: 补充最终工程化重构记录

---

## 技术要点总结

### 空间复杂度分析

| 版本 | 空间复杂度 | 最大处理长度 | 说明 |
|------|-----------|-------------|------|
| 递归版本 | O(N) | ~20000字符 | 栈深度与表达式长度成正比 |
| 循环版本 | O(1) | 无限制 | 常量栈空间，无溢出风险 |

### 错误处理机制

```
错误类型判断流程:
┌─────────────────────────────────────────────────────────────┐
│  输入字符                                                    │
│      ↓                                                       │
│  isValidToken()? ──否──→ 词法错误 (LEXICAL_ERROR)           │
│      │                                                       │
│     是                                                       │
│      ↓                                                       │
│  语法规则检查 ──违反──→ 语法错误 (SYNTAX_ERROR)              │
│      │                                                       │
│     符合                                                     │
│      ↓                                                       │
│  正常处理                                                    │
└─────────────────────────────────────────────────────────────┘
```

### Panic-Mode 恢复算法

```java
private void skipInvalidTokens() throws IOException {
    while (!isEndMarker() && !isValidToken()) {
        // 记录错误
        errors.add(new CompileError(...));
        // 跳过非法字符
        advance();
    }
    // 到达同步记号，继续分析
}
```

---

## 项目文件清单

### 源代码
- `src/Postfix.java` - 主程序（重构后的 Parser 类）
- `src/ParserTest.java` - JUnit 单元测试类
- `src/PerformanceTest.java` - 性能测试类

### 脚本文件 (scripts/)
- `build.bat` - 编译脚本
- `run.bat` - 运行脚本
- `test.bat` - 单元测试脚本
- `perf_test.bat` - 性能测试脚本
- `doc.bat` - Javadoc 生成脚本
- `testcase.bat` - 测试用例运行脚本
- `testcase-001~004.bat` - 单个测试用例脚本
- `plot_perf.py` - Python 可视化脚本

### 数据与图片
- `data/perf_results.csv` - 性能测试数据
- `img/performance_chart.png` - 性能对比图表
- `img/junit_pass.png` - JUnit 测试截图
- `img/error_lexical.png` - 词法错误截图
- `img/error_syntax_missing.png` - 缺少运算量错误截图
- `img/error_syntax_consecutive.png` - 连续运算符错误截图
- `img/error_panic_mode.png` - Panic-Mode 恢复截图

### 文档
- `design.tex` / `design.pdf` - 实验报告
- `readme.txt` - 项目说明文件
- `TODO.md` - 待办事项清单
- `memory_bank.md` - 项目记忆库

---

## 开发日志

| 日期 | 阶段 | 完成内容 |
|------|------|---------|
| 2026-04-23 | 第一阶段 | 核心代码重构（静态→非静态、尾递归消除、错误处理） |
| 2026-04-23 | 第二阶段 | JUnit 单元测试编写，21个测试全部通过 |
| 2026-04-23 | 第三阶段 | 性能测试脚本设计，CSV 数据持久化 |
| 2026-04-23 | 第四阶段 | Python 可视化脚本，生成性能图表 |
| 2026-04-27 | 第五阶段 | 工程化重构，脚本整合至 scripts/ 目录 |
| 2026-04-27 | 最终收尾 | 文档同步更新，项目准备提交 |

---

*最后更新：2026年4月27日*