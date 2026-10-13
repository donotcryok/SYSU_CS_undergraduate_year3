# TODO - 编译原理实验：后缀表达式 Postfix

## 🎉 所有 TODO 任务均已圆满完成，项目准备就绪，可以打包提交！

---

## ✅ 已完成任务清单

### 一、环境准备
- [x] JUnit 库下载：`lib/junit-4.13.2.jar` 和 `lib/hamcrest-core-1.3.jar` 已存在

### 二、编译与基础测试
- [x] 编译项目：`scripts\build.bat` 执行成功
- [x] 运行主程序：`scripts\run.bat` 基础功能正常

### 三、性能自动化测试与画图
- [x] 运行 Java 性能测试：`scripts\perf_test.bat` 生成 CSV 数据
- [x] 运行 Python 可视化：`python scripts\plot_perf.py` 生成图表
- [x] CSV 数据文件：`data/perf_results.csv` 已生成
- [x] 性能图表：`img/performance_chart.png` 已生成（183KB）

### 四、错误处理实弹测试与截图
- [x] 词法错误测试截图：`img/error_lexical.png`
- [x] 语法错误（缺少运算量）截图：`img/error_syntax_missing.png`
- [x] 语法错误（连续运算符）截图：`img/error_syntax_consecutive.png`
- [x] Panic-Mode 恢复截图：`img/error_panic_mode.png`

### 五、JUnit 单元测试
- [x] 运行单元测试：`scripts\test.bat` 21 个测试全部通过
- [x] 测试截图：`img/junit_pass.png`

### 六、实验报告撰写
- [x] 更新 `design.tex` 项目结构说明
- [x] 插入性能测试图表
- [x] 插入错误处理截图
- [x] 插入 JUnit 测试截图
- [x] 填写个人信息（学号、姓名等）
- [x] 编译 PDF：`design.pdf` 已生成

### 七、工程化重构
- [x] 移动所有 `.bat` 脚本到 `scripts/` 目录
- [x] 修复脚本相对路径（添加 `cd /d "%~dp0.."`）
- [x] 更新 `readme.txt` 目录结构
- [x] 更新 `design.tex` 项目结构说明

### 八、状态文档更新
- [x] 更新 `TODO.md` 标记完成状态
- [x] 更新 `memory_bank.md` 补充最终重构记录

---

## 📁 最终项目目录结构

```
lab3/
├── src/                      # Java 源代码
├── bin/                      # 编译输出（提交前需删除）
├── lib/                      # JUnit 依赖库
├── data/                     # 性能测试 CSV 数据
├── img/                      # 实验报告图片
├── doc/                      # Javadoc API 文档
├── testcases/                # 测试用例文件
├── scripts/                  # 所有自动化脚本（工程化整合）
│   ├── build.bat             # 编译脚本
│   ├── run.bat               # 运行脚本
│   ├── test.bat              # 单元测试脚本
│   ├── perf_test.bat         # 性能测试脚本
│   ├── doc.bat               # Javadoc 生成脚本
│   ├── testcase.bat          # 测试用例运行脚本
│   ├── testcase-001~004.bat  # 单个测试用例脚本
│   └── plot_perf.py          # Python 可视化脚本
├── design.tex                # 实验报告 LaTeX 源文件
├── design.pdf                # 实验报告 PDF（已编译）
├── readme.txt                # 项目说明文件
├── TODO.md                   # 本文件
├── memory_bank.md            # 项目记忆库
└── Lab03-Postfix.pdf         # 实验指导书
```

---

## 🚀 提交前检查清单

1. **删除编译产物**：删除 `bin/` 目录
2. **确认图片完整**：检查 `img/` 目录下所有截图是否存在
3. **确认 PDF 生成**：检查 `design.pdf` 是否最新
4. **打包命名规范**：`Lab03-Postfix-姓名-学号.zip`

---

## 📊 性能测试关键结论

| 表达式长度 | 递归版本 | 循环版本 | 结论 |
|-----------|---------|---------|------|
| 10000 | 正常 (3ms) | 正常 (3ms) | 两者相当 |
| 20000 | **StackOverflowError** | 正常 (0ms) | 递归栈溢出 |
| 100000 | 无法运行 | 正常 (11ms) | 循环版本优势明显 |

**核心结论**：在 JVM 不支持尾递归优化的情况下，手动消除尾递归是必要的。循环版本空间复杂度 O(1)，可处理任意长度表达式。

---

*最后更新时间：2026年4月27日*
