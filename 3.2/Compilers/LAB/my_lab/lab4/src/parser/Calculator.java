/**
 * @Copyright(C) 2008 Software Engineering Laboratory (SELAB), Department of Computer 
 * Science, SUN YAT-SEN UNIVERSITY. All rights reserved.
 **/

package parser;

import exceptions.*;

/**
 * ExprEval 表达式计算器的主程序入口。
 * <p>
 * 本类的 {@link #calculate(String)} 方法是 GUI 和测试框架调用的唯一入口。
 * 内部通过 {@link Scanner} 进行词法分析，再通过 {@link Parser}（算符优先分析器）
 * 进行语法分析和语义求值。
 *
 * @author 马福泉
 * @version 1.0
 **/
public class Calculator
{
	/**
	 * 计算表达式的主方法。
	 * <p>
	 * 工作流程：
	 * <ol>
	 *   <li>使用 {@link Scanner} 对输入字符串进行词法分析，生成 Token 流。</li>
	 *   <li>使用 {@link Parser} 对 Token 流进行算符优先语法分析，同步求值。</li>
	 *   <li>返回计算结果（double）。</li>
	 * </ol>
	 *
	 * @param expression 用户输入的表达式字符串（来自 GUI）
	 * @return 若表达式合法，返回其计算结果
	 * @throws ExpressionException 若表达式存在词法、语法或语义错误，抛出对应的子类异常
	 **/
	public double calculate(String expression) throws ExpressionException
	{
		// 第一步：词法分析 —— 构造 Scanner 并完成初始化扫描
		Scanner scanner = new Scanner(expression);

		// 第二步：语法分析 + 语义求值 —— 构造 Parser 并执行算符优先分析
		Parser parser = new Parser(scanner);

		// 第三步：返回计算结果
		return parser.parse();
	}
}
