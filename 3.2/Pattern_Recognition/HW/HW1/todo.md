# 模式识别课程第一次作业 - 人工操作指南

## 📋 作业信息
- **截止日期**: 2026年4月30日 24:00
- **提交邮箱**: pr202604@163.com
- **邮件主题**: 学号-姓名-第一次平时作业

---

## 🔧 环境准备（Windows + Python虚拟环境）

### 步骤 1: 创建 Python 虚拟环境

在项目根目录 `HW1` 下执行以下命令：

```cmd
# 创建虚拟环境（使用 Python 内置的 venv）
python -m venv venv

# 或者指定 Python 版本创建
py -3 -m venv venv
```

### 步骤 2: 激活虚拟环境

```cmd
# Windows CMD 激活虚拟环境
venv\Scripts\activate.bat

# 或者 Windows PowerShell 激活
venv\Scripts\Activate.ps1
```

激活成功后，命令行前面会显示 `(venv)` 标识。

**注意**: 如果 PowerShell 报错无法运行脚本，请先执行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 步骤 3: 安装依赖库

在激活虚拟环境后，执行以下命令安装所需依赖：

```cmd
pip install numpy opencv-python scipy scikit-image matplotlib
```

或者创建 `requirements.txt` 文件后安装：

```cmd
# 创建 requirements.txt（可选）
echo numpy > requirements.txt
echo opencv-python >> requirements.txt
echo scipy >> requirements.txt
echo scikit-image >> requirements.txt
echo matplotlib >> requirements.txt

# 安装依赖
pip install -r requirements.txt
```

### 步骤 4: 验证安装

```cmd
python -c "import cv2; import numpy; import scipy; import skimage; print('所有依赖安装成功！')"
```

---

## 🚀 运行 Python 脚本

### 重要提示
**所有命令都需要在虚拟环境激活状态下执行！**

确保命令行显示 `(venv)` 标识后再运行脚本。

### Task 1: Harris 角点检测
```cmd
cd src
python harris.py
```
**预期输出**: `results/1/sudoku_keypoints.png`

### Task 2: 特征提取与匹配
```cmd
python feature_match.py
```
**预期输出**: 
- `results/1/uttower_match_sift.png`
- `results/1/uttower_match_hog.png`
- `results/1/uttower_match.png`

### Task 3: 两图拼接
```cmd
python stitch.py
```
**预期输出**: 
- `results/1/uttower_stitching_sift.png`
- `results/1/uttower_stitching_hog.png`

### Task 4: 多图拼接
```cmd
python multi_stitch.py
```
**预期输出**: `results/1/yosemite_stitching.png`

### 一键运行所有任务
```cmd
python main.py
```

运行完成后，返回项目根目录：
```cmd
cd ..
```

---

## 📸 结果图复制到 LaTeX 报告目录

运行完所有脚本后，将结果图复制到 `img/` 目录：

### Windows CMD
```cmd
mkdir img
copy results\1\sudoku_keypoints.png img\
copy results\1\uttower_match.png img\
copy results\1\uttower_match_sift.png img\
copy results\1\uttower_match_hog.png img\
copy results\1\uttower_stitching_sift.png img\
copy results\1\uttower_stitching_hog.png img\
copy results\1\yosemite_stitching.png img\
```

### Windows PowerShell
```powershell
New-Item -ItemType Directory -Force -Path img
Copy-Item results\1\sudoku_keypoints.png img\
Copy-Item results\1\uttower_match.png img\
Copy-Item results\1\uttower_match_sift.png img\
Copy-Item results\1\uttower_match_hog.png img\
Copy-Item results\1\uttower_stitching_sift.png img\
Copy-Item results\1\uttower_stitching_hog.png img\
Copy-Item results\1\yosemite_stitching.png img\
```

---

## 📝 编译 LaTeX 报告

### 方法 1: 使用 XeLaTeX（推荐，支持中文）
```cmd
xelatex lab1.tex
```

### 方法 2: 使用 VS Code LaTeX Workshop 插件
直接在 VS Code 中打开 `lab1.tex`，点击右上角的绿色播放按钮编译。

### 注意事项
- 确保已安装 LaTeX 发行版（如 TeX Live 或 MiKTeX）
- 确保已安装中文支持包（ctex）
- 需要将 `SYSULogo.png` 放入 `img/` 目录（如果使用校徽）

---

## 📦 打包提交

### 打包内容
确保以下文件/目录包含在压缩包中：
- `src/` - 源代码目录
- `images/` - 输入图像目录
- `results/` - 输出结果目录
- `img/` - 报告插图目录
- `lab1.tex` - LaTeX 源码
- `lab1.pdf` - 编译后的 PDF 报告
- `memory_bank.md` - 项目记忆库
- `todo.md` - 本文件
- `venv/` - **不需要包含**（虚拟环境不打包）

### Windows PowerShell 打包命令
```powershell
# 先编译生成 PDF
xelatex lab1.tex

# 创建 zip 压缩包
Compress-Archive -Path src,images,results,img,lab1.tex,lab1.pdf,memory_bank.md,todo.md -DestinationPath 学号-姓名-第一次平时作业.zip -Force
```

### Windows CMD 打包（使用 7-Zip 或 WinRAR）
如果安装了 7-Zip：
```cmd
xelatex lab1.tex
7z a 学号-姓名-第一次平时作业.zip src images results img lab1.tex lab1.pdf memory_bank.md todo.md
```

---

## ✅ 提交前检查清单

- [ ] 创建并激活 Python 虚拟环境
- [ ] 安装所有依赖库
- [ ] 所有 Python 脚本运行无错误
- [ ] `results/1/` 目录下生成了所有预期结果图
- [ ] 结果图已复制到 `img/` 目录
- [ ] LaTeX 报告编译成功，生成 `lab1.pdf`
- [ ] 报告中所有图片正确显示
- [ ] 报告中代码展示部分格式正确
- [ ] 压缩包命名格式正确：`学号-姓名-第一次平时作业.zip`
- [ ] 邮件主题格式正确：`学号-姓名-第一次平时作业`
- [ ] 在截止日期前发送邮件至 `pr202604@163.com`

---

## ⚠️ 常见问题

### Q1: 虚拟环境激活失败
**解决方案**: 
- 确保使用正确的激活脚本路径 `venv\Scripts\activate.bat`
- PowerShell 用户需要先设置执行策略

### Q2: 运行脚本时提示找不到模块
**解决方案**: 
- 确保虚拟环境已激活（命令行显示 `(venv)`）
- 在虚拟环境中重新安装依赖

### Q3: LaTeX 编译报错
**解决方案**: 
- 确保安装了 TeX Live 或 MiKTeX
- 确保安装了中文支持包（ctex）
- 使用 XeLaTeX 编译而非 pdflatex

### Q4: 结果图显示异常
**解决方案**: 
- 检查输入图像路径是否正确（`images/1/` 目录）
- 检查图像文件是否损坏
- 查看终端输出的错误信息

### Q5: Harris 角点检测结果角点过多或过少
**解决方案**: 
- 调整 `harris.py` 中的阈值参数
- 调整非极大值抑制窗口大小

### Q6: 退出虚拟环境
```cmd
deactivate
```

---

## 📧 联系方式
如有问题，请联系课程助教或在课程群内咨询。

**祝实验顺利！** 🎉