"""
ViLT 视觉问答 (VQA) 推理脚本
作者: 马福泉
学号: 23336179
日期: 2026年4月
"""

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import warnings
from typing import Optional, List, Dict
from PIL import Image
import torch
from datetime import datetime

# 忽略一些不必要的警告信息
warnings.filterwarnings('ignore')


class VQA_Model:
    """
    ViLT 视觉问答模型类
    该类封装了 ViLT 模型的加载和推理功能，提供简洁的接口进行图文问答。
    """
    
    def __init__(self, model_name: str = "dandelin/vilt-b32-finetuned-vqa"):
        """
        初始化 VQA 模型
        Args: model_name (str): Hugging Face 上的模型名称，默认为 VQA 微调版本
        """
        self.model_name = model_name
        self.device = self._get_device()
        self.processor = None
        self.model = None
        
        print(f"[INFO] 正在初始化 ViLT VQA 模型...")
        print(f"[INFO] 模型名称: {self.model_name}")
        print(f"[INFO] 计算设备: {self.device}")
        print(f"[INFO] 使用镜像源: {os.environ.get('HF_ENDPOINT', 'default')}")
        
        self._load_processor()
        self._load_model()
        
        print(f"[INFO] 模型加载完成！\n")
    
    def _get_device(self) -> str:
        """检测并返回可用的计算设备"""
        if torch.cuda.is_available():
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'
        else:
            return 'cpu'
    
    def _load_processor(self):
        """加载 ViLT 处理器 (Processor)"""
        from transformers import ViltProcessor
        
        print(f"[INFO] 正在加载 ViltProcessor...")
        self.processor = ViltProcessor.from_pretrained(self.model_name)
        print(f"[INFO] ViltProcessor 加载成功")
    
    def _load_model(self):
        """加载 ViLT 问答模型"""
        from transformers import ViltForQuestionAnswering
        
        print(f"[INFO] 正在加载 ViltForQuestionAnswering 模型...")
        self.model = ViltForQuestionAnswering.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        print(f"[INFO] ViltForQuestionAnswering 模型加载成功")
    
    def predict_answer(
        self, 
        image_path: str, 
        question: str,
        top_k: int = 5
    ) -> List[Dict[str, float]]:
        """
        根据图像和问题预测答案
        Args:
            image_path (str): 图像文件路径
            question (str): 文本问题
            top_k (int): 返回前 k 个最可能的答案
        Returns:
            List[Dict[str, float]]: 包含答案和置信度的列表
        """
        self._validate_inputs(image_path, question)
        image = self._load_image(image_path)
        
        encoding = self.processor(
            image,
            question,
            return_tensors="pt"
        )
        
        encoding = {k: v.to(self.device) for k, v in encoding.items()}
        
        with torch.no_grad():
            outputs = self.model(**encoding)
        
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=-1)
        top_k_probs, top_k_indices = torch.topk(probs[0], min(top_k, probs.size(-1)))
        
        results = []
        for prob, idx in zip(top_k_probs, top_k_indices):
            answer = self.model.config.id2label[idx.item()]
            confidence = prob.item()
            results.append({
                "answer": answer,
                "confidence": confidence
            })
        
        return results
    
    def _validate_inputs(self, image_path: str, question: str):
        """验证输入参数的有效性"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"找不到图像文件 '{image_path}'")
        
        if not question or not question.strip():
            raise ValueError("问题不能为空")
        
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in valid_extensions:
            raise ValueError(f"不支持的图像格式 '{ext}'")
    
    def _load_image(self, image_path: str) -> Image.Image:
        """加载图像文件"""
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        except Exception as e:
            raise ValueError(f"无法加载图像 '{image_path}'\n原因: {str(e)}")


class ResultLogger:
    """
    将测试结果同时输出到控制台和文件
    """
    
    def __init__(self, output_file: str = "result.txt"):
        """
        初始化日志记录器
        
        Args:
            output_file (str): 输出文件路径
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_path = os.path.join(current_dir, output_file)
        self.results = []
        
        # 初始化输出文件，写入头部信息
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("          ViLT 视觉问答 (VQA) 测试结果报告\n")
            f.write("=" * 70 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"模型: dandelin/vilt-b32-finetuned-vqa\n")
            f.write("=" * 70 + "\n\n")
    
    def log_image_header(self, image_name: str, image_desc: str = ""):
        """记录图片头部信息"""
        header = "=" * 70 + "\n"
        header += f"【图片】{image_name}"
        if image_desc:
            header += f" - {image_desc}"
        header += "\n" + "=" * 70 + "\n"
        
        print(header)
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write(header)
    
    def log_question(self, question: str):
        """记录问题"""
        content = f"\n【问题】{question}\n"
        content += "-" * 70 + "\n"
        
        print(content)
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write(content)
    
    def log_results(self, results: List[Dict[str, float]]):
        """记录预测结果"""
        content = ""
        for i, result in enumerate(results, 1):
            line = f"  {i}. 【答案】{result['answer']}\n"
            line += f"     【置信度】{result['confidence']:.2%}\n"
            content += line
            print(line.rstrip())
        
        content += "\n"
        print()
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write(content)
    
    def log_error(self, error_msg: str):
        """记录错误信息"""
        content = f"  [错误] {error_msg}\n\n"
        print(content)
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write(content)
    
    def log_warning(self, warning_msg: str):
        """记录警告信息"""
        content = f"  [警告] {warning_msg}\n\n"
        print(content)
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write(content)
    
    def log_summary(self, success_count: int, total_questions: int, total_images: int):
        """记录统计摘要"""
        content = "=" * 70 + "\n"
        content += "【测试统计】\n"
        content += "=" * 70 + "\n"
        content += f"  成功处理: {success_count}/{total_questions} 个问题\n"
        content += f"  测试图片: {total_images} 张\n"
        content += "=" * 70 + "\n"
        
        print(content)
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write(content)
    
    def log_section(self, title: str):
        """记录章节标题"""
        content = "\n" + "=" * 70 + "\n"
        content += f"  {title}\n"
        content += "=" * 70 + "\n\n"
        
        print(content)
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write(content)


def get_test_matrix() -> Dict[str, Dict]:
    """
    获取测试矩阵配置:
        Dict[str, Dict]: 测试配置字典
    """
    return {
        "1.jpg": {
            "description": "基础单目标 - 猫",
            "questions": [
                "What kind of animal is in this picture?",
                "What color is the animal?",
                "Is the animal cute?"
            ]
        },
        "2.jpg": {
            "description": "基础单目标 - 狗",
            "questions": [
                "What kind of animal is in this picture?",
                "What color is the dog?",
                "Is this a pet?"
            ]
        },
        "3.jpg": {
            "description": "基础单目标 - 狗",
            "questions": [
                "What animal is this?",
                "What is the dog doing?",
                "Is the dog sitting?"
            ]
        },
        "4.jpg": {
            "description": "基础单目标 - 奔跑的狗",
            "questions": [
                "What kind of animal is in this picture?",
                "What is the animal doing?",
                "What color is the dog?"
            ]
        },
        "5.jpg": {
            "description": "多物种同框 - 猫和狗",
            "questions": [
                "What animals are in the picture?",
                "How many animals are there?",
                "Are there both a cat and a dog in this picture?"
            ]
        },
        "6.jpg": {
            "description": "密集目标 - 多只金毛幼犬",
            "questions": [
                "What kind of animal is in this picture?",
                "How many animals are there in total?"
            ]
        },
        "7.jpg": {
            "description": "人宠交互 - 一家人和一只狗",
            "questions": [
                "How many people are in the picture?",
                "What kind of animal is in the picture?",
                "How many animals are there?"
            ]
        }
    }


def batch_test(model: VQA_Model):
    """
    批量测试函数: 对 7 张图片进行复杂场景问答测试
    Args:
        model (VQA_Model): 已加载的 VQA 模型实例
    """
    # 获取路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), "data")
    
    # 初始化日志记录器
    logger = ResultLogger("result.txt")
    
    # 获取测试矩阵
    test_matrix = get_test_matrix()
    
    # 记录测试开始
    logger.log_section("ViLT 视觉问答 (VQA) 复杂场景批量测试")
    
    success_count = 0
    total_questions = 0
    processed_images = 0
    
    # 遍历每个测试用例
    for image_name, config in test_matrix.items():
        image_path = os.path.join(data_dir, image_name)
        image_desc = config.get("description", "")
        questions = config.get("questions", [])
        
        # 记录图片信息
        logger.log_image_header(image_name, image_desc)
        
        # 检查图片是否存在
        if not os.path.exists(image_path):
            logger.log_warning(f"图片不存在: {image_path}")
            continue
        
        processed_images += 1
        
        # 对每个问题进行预测
        for question in questions:
            total_questions += 1
            logger.log_question(question)
            
            try:
                # 获取预测结果
                results = model.predict_answer(image_path, question, top_k=3)
                logger.log_results(results)
                success_count += 1
                
            except Exception as e:
                logger.log_error(str(e))
    
    # 记录统计摘要
    logger.log_summary(success_count, total_questions, processed_images)
    
    print(f"\n[INFO] 测试结果已保存到: {logger.output_path}")


def main():
    """
    主函数: 执行 ViLT VQA 复杂场景测试
    """
    print("\n" + "=" * 70)
    print(" " * 15 + "ViLT 视觉问答 (VQA) 演示程序")
    print(" " * 10 + "模型: dandelin/vilt-b32-finetuned-vqa")
    print(" " * 10 + "测试场景: 基础单目标 + 多物种 + 密集目标 + 人宠交互")
    print("=" * 70)
    print()
    
    # 初始化模型
    vqa_model = VQA_Model()
    
    # 执行批量测试
    batch_test(vqa_model)
    
    print("\n演示结束！")


if __name__ == "__main__":
    main()