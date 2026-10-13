# 待办事项 (TODO)

## 环境配置

### 1. 创建虚拟环境
打开终端，在项目根目录 `e:/3.2/Pattern_Recognition/HW/HW2` 下执行：

```cmd
python -m venv venv
```

### 2. 激活虚拟环境

**Windows (cmd.exe):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

### 3. 安装依赖库
激活虚拟环境后，执行以下命令安装所有依赖：

```cmd
pip install numpy scipy Pillow matplotlib
```

> **说明：**
> - `numpy`: 矩阵运算、SVD 分解
> - `scipy`: 读取 `.mat` 格式的人脸数据集
> - `Pillow`: RGB 图像读写
> - `matplotlib`: 结果可视化与图片保存

### 4. 验证安装
执行以下命令确认所有包已正确安装：

```cmd
python -c "import numpy; import scipy; import PIL; import matplotlib; print('All dependencies installed successfully!')"
```

## 运行实验

### 运行人脸压缩实验
```cmd
cd e:/3.2/Pattern_Recognition/HW/HW2
python src/face_task.py
```

### 运行彩色图像压缩实验
```cmd
python src/rgb_task.py
```

## 编译 LaTeX 报告
使用 XeLaTeX 编译实验报告（需要安装 TeX Live 或 MiKTeX）：

```cmd
xelatex lab2.tex
```

> 如果图片引用有问题，可能需要编译两次以正确生成交叉引用。

## 注意事项
- 如果 `faces.mat` 读取失败，请检查 `data/faces.mat` 文件是否完整。
- 彩色图像文件名为 `data/woman.png`（而非 `woman.jpg`），脚本中已做相应处理。
- 生成的图片将保存在 `img/` 目录下，请确保该目录存在。
