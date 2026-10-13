/**
 * ExprEval 的语法分析器，基于算符优先分析（Operator Precedence Parsing，OPP）实现。
 * <p>
 * 本分析器消费 {@link Scanner} 产生的 Token 流，通过算符优先关系矩阵驱动移进-归约过程，
 * 并在每次归约时同步执行语义动作（求值）。核心功能包括：
 * <ul>
 *   <li><b>算符优先分析</b>：利用优先关系表决定移进（shift）还是归约（reduce）。</li>
 *   <li><b>一元取负识别</b>：通过前驱 Token 上下文自动区分一元取负（NEG）与二元减法（SUB）。</li>
 *   <li><b>三元运算符 {@code ?:}</b>：右结合，条件必须为布尔类型，分支必须为数值类型。</li>
 *   <li><b>预定义函数调用</b>：支持 9 个预定义函数，自动检查参数个数与类型。</li>
 *   <li><b>类型检查</b>：布尔值只能参与逻辑运算（{@code &, |, !, ~}）和三元条件，不能用于算术运算。</li>
 * </ul>
 * <p>
 * <b>优先级层次</b>（从低到高）：
 * <ol>
 *   <li>{@code ?:} （三元条件，右结合）</li>
 *   <li>{@code &, |} （逻辑与/或，左结合）</li>
 *   <li>{@code !, ~} （逻辑非/按位非，一元前缀）</li>
 *   <li>{@code <, >, <=, >=, ==, !=} （关系比较，左结合）</li>
 *   <li>{@code +, -} （加减，左结合）</li>
 *   <li>{@code *, /} （乘除，左结合）</li>
 *   <li>{@code ^} （幂，右结合）</li>
 *   <li>{@code -} （一元取负 NEG，右结合）</li>
 *   <li>函数调用、括号</li>
 * </ol>
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package parser;

import java.util.ArrayList;
import java.util.List;
import java.util.Stack;

import exceptions.*;
import parser.Scanner.Token;
import parser.Scanner.TokenType;

public class Parser
{
	// ==================== 常量与数据结构 ====================

	/** 值栈上的哨兵标记，用于界定函数参数或括号子表达式的起始位置。 */
	private static final Object 哨兵 = new Object();

	/** 存储中间结果的值栈。元素为 {@link Double}、{@link Boolean} 或 {@link #哨兵}。 */
	private Stack<Object> 值栈;

	/** 运算符栈。存储算符字符串标识（如 {@code "+"}、{@code "NEG"}、{@code "?:"}）及障碍符（{@code "("}、函数标记）。 */
	private Stack<String> 算符栈;

	/** 词法扫描器，提供 Token 流。 */
	private Scanner scanner;

	/**
	 * 前一 Token 是否为一个完整的操作数。
	 * <p>
	 * 用于区分一元取负（NEG）与二元减法（SUB）：
	 * 若前驱不是操作数，则 {@code -} 被判定为一元取负。
	 */
	private boolean 前驱是操作数;

	// ==================== 构造器 ====================

	/**
	 * 使用给定的 Scanner 构造语法分析器。
	 *
	 * @param scanner 已完成初始化的词法扫描器
	 */
	public Parser(Scanner scanner)
	{
		this.scanner = scanner;
		this.值栈 = new Stack<Object>();
		this.算符栈 = new Stack<String>();
		this.前驱是操作数 = false;
		// 推入哨兵 "#"，作为算符栈底标志
		算符栈.push("#");
	}

	// ==================== 公开入口 ====================

	/**
	 * 执行算符优先分析，返回表达式的计算结果。
	 *
	 * @return 表达式求值结果（double）
	 * @throws ExpressionException 词法、语法或语义错误时抛出相应异常
	 */
	public double parse() throws ExpressionException
	{
		while (true)
		{
			Token token = scanner.peek();

			switch (token.type)
			{
				case EOF:
					return 处理EOF();

				case NUMBER:
					处理操作数(token.numValue, false);
					break;

				case BOOLEAN:
					处理操作数(token.boolValue ? 1.0 : 0.0, true);
					break;

				case IDENTIFIER:
					处理函数调用(token.lexeme);
					break;

				case LPAREN:
					处理左括号();
					break;

				case RPAREN:
					处理右括号();
					break;

				case COMMA:
					处理逗号();
					break;

				case QUEST:
					处理问号();
					break;

				case COLON:
					处理冒号();
					break;

				default:
					// 其余均为运算符
					String 算符 = 映射算符(token.type);
					处理运算符(算符);
					break;
			}
		}
	}

	// ==================== Token 类型到算符字符串的映射 ====================

	/**
	 * 将 TokenType 映射为算符栈上使用的字符串标识。
	 * <p>
	 * 特别地，{@code SUB} 需要调用方根据上下文决定返回 {@code "-"} 还是 {@code "NEG"}；
	 * 本方法默认返回 {@code "-"}。
	 *
	 * @param type Token 类型
	 * @return 对应的算符字符串
	 */
	private String 映射算符(TokenType type)
	{
		switch (type)
		{
			case PLUS:    return "+";
			case SUB:     return "-";     // 由调用方根据上下文覆盖为 "NEG"
			case MUL:     return "*";
			case DIV:     return "/";
			case POW:     return "^";
			case AND:     return "&";
			case OR:      return "|";
			case NOT:     return "!";
			case BIT_NOT: return "~";
			case LT:      return "<";
			case GT:      return ">";
			case LE:      return "<=";
			case GE:      return ">=";
			case EQ:      return "==";
			case NE:      return "!=";
			default:
				throw new IllegalArgumentException("非运算符 Token 类型: " + type);
		}
	}

	// ==================== 各 Token 的处理方法 ====================

	/**
	 * 将操作数压入值栈。
	 *
	 * @param value      数值（double）或布尔值（boolean 以 double 形式传入，0.0=false，1.0=true）
	 * @param isBoolean  是否为布尔类型
	 * @throws MissingOperatorException 若前一个 Token 也是操作数（缺少运算符连接）
	 */
	private void 处理操作数(double value, boolean isBoolean)
		throws MissingOperatorException, LexicalException
	{
		if (前驱是操作数)
		{
			throw new MissingOperatorException("缺少运算符：两个操作数之间需要运算符连接");
		}

		if (isBoolean)
		{
			值栈.push(Boolean.valueOf(value != 0.0));
		}
		else
		{
			值栈.push(Double.valueOf(value));
		}

		scanner.advance();
		前驱是操作数 = true;
	}

	/**
	 * 处理左括号 {@code (}。
	 * <p>
	 * 将 {@code "("} 压入算符栈，同时在值栈上压入哨兵，用于后续边界检测。
	 */
	private void 处理左括号() throws LexicalException
	{
		算符栈.push("(");
		值栈.push(哨兵);
		scanner.advance();
		前驱是操作数 = false;
	}

	/**
	 * 处理右括号 {@code )}。
	 * <p>
	 * 归约所有算符直到遇到匹配的 {@code "("} 或函数标记。
	 * <ul>
	 *   <li>若遇到 {@code "("}：弹出左括号及值栈哨兵。</li>
	 *   <li>若遇到函数标记：收集参数、检查参数个数、执行函数调用。</li>
	 * </ul>
	 *
	 * @throws ExpressionException 括号不匹配、缺少操作数或函数调用错误时抛出
	 */
	private void 处理右括号() throws ExpressionException
	{
		// 先归约直至遇到障碍符
		归约至障碍符();

		String 栈顶 = 算符栈.peek();

		if (栈顶.equals("("))
		{
			// 普通括号：先弹出归约结果（在哨兵之上），再弹出哨兵，最后把结果压回
			算符栈.pop();

			// 收集括号内归约的结果（恰好一个值在哨兵之上）
			Object 括号结果 = null;
			while (!值栈.isEmpty() && 值栈.peek() != 哨兵)
			{
				if (括号结果 != null)
				{
					throw new MissingOperatorException(
						"括号内表达式不完整：存在多余的操作数，缺少运算符");
				}
				括号结果 = 值栈.pop();
			}

			// 弹出哨兵
			弹出哨兵(")");

			// 将括号内表达式的值压回值栈（若括号内有表达式）
			if (括号结果 != null)
			{
				值栈.push(括号结果);
			}

			scanner.advance();
			前驱是操作数 = true;
		}
		else if (栈顶.startsWith("FUNC:"))
		{
			// 函数调用：收集参数并求值
			执行函数调用();
			scanner.advance();
			前驱是操作数 = true;
		}
		else
		{
			throw new MissingLeftParenthesisException(
				"缺少匹配的左括号：多余的 ')'");
		}
	}

	/**
	 * 处理逗号 {@code ,}（函数参数分隔符）。
	 * <p>
	 * 将当前已归约的参数保留在值栈上，归约至函数标记处但不弹出标记。
	 *
	 * @throws ExpressionException 逗号位置非法时抛出
	 */
	private void 处理逗号() throws ExpressionException
	{
		// 归约至最近的障碍符（函数标记或左括号）
		归约至障碍符();

		String 栈顶 = 算符栈.peek();
		if (!栈顶.startsWith("FUNC:"))
		{
			throw new FunctionCallException("逗号 ',' 只能出现在函数参数列表中");
		}

		// 逗号本身不入栈，仅前进并继续解析下一个参数
		scanner.advance();
		前驱是操作数 = false;
	}

	/**
	 * 处理问号 {@code ?}（三元条件运算符的条件部分）。
	 * <p>
	 * 归约所有优先级高于 {@code "?"} 的算符，然后将 {@code "?"} 压栈。
	 *
	 * @throws ExpressionException 归约过程中可能抛出的异常
	 */
	private void 处理问号() throws ExpressionException
	{
		// "?" 优先级很低（level 2），先归约所有更高优先级的算符
		while (!是障碍符(算符栈.peek()) && 比较优先级(算符栈.peek(), "?") == '>')
		{
			归约();
		}

		if (前驱是操作数)
		{
			算符栈.push("?");
			scanner.advance();
			前驱是操作数 = false;
		}
		else
		{
			throw new MissingOperandException(
				"三元运算符 '?' 之前缺少条件表达式");
		}
	}

	/**
	 * 处理冒号 {@code :}（三元条件运算符的分支分隔符）。
	 * <p>
	 * 在算符栈上寻找匹配的 {@code "?"}，将其替换为 {@code "?:"}，
	 * 然后继续解析第二个分支。
	 *
	 * @throws ExpressionException 缺少匹配的 {@code "?"} 时抛出
	 */
	private void 处理冒号() throws ExpressionException
	{
		// 归约直到遇到 "?" 或障碍符
		while (!是障碍符(算符栈.peek()) && !算符栈.peek().equals("?"))
		{
			归约();
		}

		String 栈顶 = 算符栈.peek();
		if (栈顶.equals("?"))
		{
			// 将 "?" 替换为 "?:"，表示已完成条件与第一分支的解析
			算符栈.pop();
			算符栈.push("?:");
			scanner.advance();
			前驱是操作数 = false;
		}
		else
		{
			throw new TrinaryOperationException(
				"三元运算符 ':' 缺少匹配的 '?'");
		}
	}

	/**
	 * 处理通用二元或一元运算符。
	 * <p>
	 * 特别地，若当前 Token 为 {@code SUB} 且前驱不是操作数，
	 * 则将其识别为一元取负 {@code "NEG"}。
	 *
	 * @param 算符 算符字符串标识
	 * @throws ExpressionException 语法或语义错误时抛出
	 */
	private void 处理运算符(String 算符) throws ExpressionException
	{
		// 一元取负上下文判断
		if (算符.equals("-") && !前驱是操作数)
		{
			算符 = "NEG";
		}

		// 对于二元运算符，若前驱不是操作数则报错（一元操作符 "!", "~", "NEG" 除外）
		if (!是合法一元前缀(算符) && !前驱是操作数)
		{
			throw new MissingOperandException(
				"运算符 '" + 算符 + "' 之前缺少操作数");
		}

		// 按优先关系归约，直到栈顶算符优先级低于当前算符
		while (!是障碍符(算符栈.peek()) && 比较优先级(算符栈.peek(), 算符) == '>')
		{
			归约();
		}

		// 压入当前算符
		算符栈.push(算符);
		scanner.advance();
		前驱是操作数 = false;
	}

	/**
	 * 处理 EOF：归约所有剩余算符，检查并返回最终结果。
	 *
	 * @return 表达式计算结果
	 * @throws ExpressionException 表达式不完整或存在未配对的符号时抛出
	 */
	private double 处理EOF() throws ExpressionException
	{
		// 归约所有算符，直到只剩哨兵 "#"
		while (!算符栈.peek().equals("#"))
		{
			String 栈顶 = 算符栈.peek();

			// 检查是否为未闭合的构造（障碍符或特殊的 "?" 标记）
			if (栈顶.equals("?"))
			{
				throw new TrinaryOperationException(
					"三元运算符 '?:' 缺少 ':' 分支");
			}

			if (是障碍符(栈顶))
			{
				// 存在未配对的障碍符
				if (栈顶.equals("("))
				{
					throw new MissingRightParenthesisException(
						"缺少匹配的右括号 ')'");
				}
				else if (栈顶.startsWith("FUNC:"))
				{
					String 函数名 = 栈顶.substring(5);
					throw new MissingRightParenthesisException(
						"函数 '" + 函数名 + "' 调用缺少匹配的右括号 ')'");
				}
				else
				{
					throw new SyntacticException(
						"表达式不完整：未闭合的 '" + 栈顶 + "'");
				}
			}
			归约();
		}

		// 检查值栈
		if (值栈.isEmpty())
		{
			throw new EmptyExpressionException("表达式为空");
		}

		// 弹出哨兵
		算符栈.pop();

		// 检查最终结果
		if (值栈.size() != 1)
		{
			throw new MissingOperatorException(
				"表达式不完整：存在多余的操作数，缺少运算符");
		}

		Object 结果 = 值栈.pop();

		// 检查是否有遗留的哨兵
		if (结果 == 哨兵)
		{
			throw new MissingOperandException("表达式不完整：缺少操作数");
		}

		if (结果 instanceof Boolean)
		{
			// 布尔值不能作为表达式最终结果（calculate 返回 double）
			throw new TypeMismatchedException(
				"表达式结果不能为布尔类型（true/false），仅数值结果被接受");
		}

		return ((Double) 结果).doubleValue();
	}

	// ==================== 归约操作 ====================

	/**
	 * 从算符栈弹出一个算符，从值栈弹出对应数量的操作数，执行语义动作，将结果压回值栈。
	 *
	 * @throws ExpressionException 语义错误（类型不匹配、除零等）时抛出
	 */
	private void 归约() throws ExpressionException
	{
		String 算符 = 算符栈.pop();

		if (是二元算符(算符))
		{
			归约二元(算符);
		}
		else if (是一元算符(算符))
		{
			归约一元(算符);
		}
		else if (算符.equals("?:"))
		{
			归约三元();
		}
		else
		{
			throw new SyntacticException("无法归约的算符: '" + 算符 + "'");
		}
	}

	/**
	 * 归约二元运算符。
	 * <p>
	 * 在弹出操作数之前先检查值栈中可用操作数数量：
	 * <ul>
	 *   <li>0 个 → 报缺左操作数</li>
	 *   <li>1 个 → 栈中唯一的操作数必然是左操作数，报缺右操作数</li>
	 *   <li>≥ 2 个 → 正常弹出右、左操作数</li>
	 * </ul>
	 */
	private void 归约二元(String 算符) throws ExpressionException
	{
		// 先检查可用操作数数量，避免"1+"时把左操作数误报为右操作数
		int 可用操作数 = 计数操作数();
		if (可用操作数 == 0)
		{
			throw new MissingOperandException("缺少操作数：" + 算符 + " 的左操作数");
		}
		if (可用操作数 == 1)
		{
			throw new MissingOperandException("缺少操作数：" + 算符 + " 的右操作数");
		}

		Object 右操作数 = 弹出操作数(算符 + " 的右操作数");
		Object 左操作数 = 弹出操作数(算符 + " 的左操作数");

		if (是算术算符(算符))
		{
			// 算术运算：+, -, *, /, ^
			double 左 = 要求数值(左操作数, 算符);
			double 右 = 要求数值(右操作数, 算符);

			double 结果;
			switch (算符)
			{
				case "+": 结果 = 左 + 右; break;
				case "-": 结果 = 左 - 右; break;
				case "*": 结果 = 左 * 右; break;
				case "/":
					if (右 == 0.0)
					{
						throw new DividedByZeroException(
							"除零错误：" + 左 + " / " + 右);
					}
					结果 = 左 / 右;
					break;
				case "^": 结果 = Math.pow(左, 右); break;
				default:
					throw new SyntacticException("未知算术算符: " + 算符);
			}
			值栈.push(Double.valueOf(结果));
		}
		else if (是关系算符(算符))
		{
			// 关系运算：<, >, <=, >= 只能用于数值比较
			// ==, != 可用于数值比较或布尔相等比较
			boolean 结果;

			if (算符.equals("==") || 算符.equals("!="))
			{
				// 先检查是否为布尔相等比较
				if (左操作数 instanceof Boolean && 右操作数 instanceof Boolean)
				{
					boolean 左 = ((Boolean) 左操作数).booleanValue();
					boolean 右 = ((Boolean) 右操作数).booleanValue();
					if (算符.equals("=="))
					{
						结果 = 左 == 右;
					}
					else
					{
						结果 = 左 != 右;
					}
				}
				else
				{
					double 左 = 要求数值(左操作数, 算符);
					double 右 = 要求数值(右操作数, 算符);
					if (算符.equals("=="))
					{
						结果 = 左 == 右;
					}
					else
					{
						结果 = 左 != 右;
					}
				}
			}
			else
			{
				double 左 = 要求数值(左操作数, 算符);
				double 右 = 要求数值(右操作数, 算符);

				switch (算符)
				{
					case "<":  结果 = 左 < 右; break;
					case ">":  结果 = 左 > 右; break;
					case "<=": 结果 = 左 <= 右; break;
					case ">=": 结果 = 左 >= 右; break;
					default:
						throw new SyntacticException("未知关系算符: " + 算符);
				}
			}
			值栈.push(Boolean.valueOf(结果));
		}
		else if (是逻辑算符(算符))
		{
			// 逻辑运算：&, |
			boolean 左 = 要求布尔(左操作数, 算符);
			boolean 右 = 要求布尔(右操作数, 算符);

			boolean 结果;
			switch (算符)
			{
				case "&": 结果 = 左 && 右; break;
				case "|": 结果 = 左 || 右; break;
				default:
					throw new SyntacticException("未知逻辑算符: " + 算符);
			}
			值栈.push(Boolean.valueOf(结果));
		}
		else
		{
			throw new SyntacticException("未知二元算符: " + 算符);
		}
	}

	/**
	 * 归约一元运算符（{@code NEG}、{@code !}、{@code ~}）。
	 */
	private void 归约一元(String 算符) throws ExpressionException
	{
		Object 操作数 = 弹出操作数(算符 + " 的操作数");

		switch (算符)
		{
			case "NEG":
			{
				double 值 = 要求数值(操作数, 算符);
				值栈.push(Double.valueOf(-值));
				break;
			}
			case "!":
			{
				boolean 值 = 要求布尔(操作数, 算符);
				值栈.push(Boolean.valueOf(!值));
				break;
			}
			case "~":
			{
				boolean 值 = 要求布尔(操作数, 算符);
				值栈.push(Boolean.valueOf(!值));
				break;
			}
			default:
				throw new SyntacticException("未知一元算符: " + 算符);
		}
	}

	/**
	 * 归约三元条件运算符 {@code ?:}。
	 * <p>
	 * 值栈布局：[..., 条件, 真分支, 假分支]（栈顶为假分支）。
	 * 条件必须为布尔类型，分支值不做类型限制但必须存在。
	 */
	private void 归约三元() throws ExpressionException
	{
		Object 假分支 = 弹出操作数("三元运算符 '?:' 的假分支");
		Object 真分支 = 弹出操作数("三元运算符 '?:' 的真分支");
		Object 条件 = 弹出操作数("三元运算符 '?:' 的条件");

		boolean 条件值 = 要求布尔(条件, "?:");

		if (条件值)
		{
			值栈.push(真分支);
		}
		else
		{
			值栈.push(假分支);
		}
	}

	// ==================== 辅助方法：归约至障碍符 ====================

	/**
	 * 持续归约直到算符栈顶为障碍符（{@code "("}、函数标记、{@code "#"}）。
	 * <p>
	 * 注意：{@code "?"} 和 {@code "?:"} 不是障碍符，在归约过程中同样会被处理。
	 *
	 * @throws ExpressionException 归约过程中的语义错误
	 */
	private void 归约至障碍符() throws ExpressionException
	{
		while (!是障碍符(算符栈.peek()))
		{
			归约();
		}
	}

	// ==================== 函数调用处理 ====================

	/**
	 * 处理函数调用：消费 IDENTIFIER Token 及随后的 LPAREN Token，
	 * 在算符栈压入函数标记，在值栈压入哨兵。
	 *
	 * @param 函数名 函数名（已转为小写）
	 * @throws ExpressionException 若标识符后不是 {@code "("}
	 */
	private void 处理函数调用(String 函数名) throws ExpressionException
	{
		// 消费标识符 Token
		scanner.advance();

		// 下一个必须是 LPAREN
		Token next = scanner.peek();
		if (next.type != TokenType.LPAREN)
		{
			throw new FunctionCallException(
				"函数 '" + 函数名 + "' 调用缺少左括号 '('");
		}

		// 消费 LPAREN
		scanner.advance();

		// 压入函数标记（以 "FUNC:" 为前缀）和哨兵
		算符栈.push("FUNC:" + 函数名);
		值栈.push(哨兵);
		前驱是操作数 = false;
	}

	/**
	 * 执行函数调用：收集参数、验证参数个数、计算结果。
	 * <p>
	 * 调用前，算符栈顶应为 {@code "FUNC:函数名"}，值栈顶为哨兵，
	 * 哨兵之上为本函数的所有实参值。
	 */
	private void 执行函数调用() throws ExpressionException
	{
		String 函数标记 = 算符栈.pop();
		String 函数名 = 函数标记.substring(5); // 去掉 "FUNC:" 前缀

		// 收集所有参数（哨兵之上的所有值）
		List<Object> 参数列表 = new ArrayList<Object>();
		while (!值栈.isEmpty() && 值栈.peek() != 哨兵)
		{
			参数列表.add(0, 值栈.pop()); // 逆序插入以保持参数原始顺序
		}

		// 弹出哨兵
		弹出哨兵("函数 " + 函数名);

		// 反转参数列表（因为我们是逆序收集的）
		// 实际上上面用 add(0, ...) 已经保持了顺序，无需再反转
		// 但为了代码可读性，确认参数顺序是从左到右的

		// 验证参数个数并求值
		double 结果 = 求值函数调用(函数名, 参数列表);
		值栈.push(Double.valueOf(结果));
	}

	/**
	 * 根据函数名检查参数个数、参数类型，并计算结果。
	 *
	 * @param 函数名   函数名
	 * @param 参数列表 实参列表（均为 {@link Double} 或 {@link Boolean}）
	 * @return 函数计算结果
	 * @throws ExpressionException 参数个数或类型错误时抛出
	 */
	private double 求值函数调用(String 函数名, List<Object> 参数列表)
		throws ExpressionException
	{
		int 参数个数 = 参数列表.size();

		// 将参数转为 double 数组（函数参数必须全为数值类型）
		double[] args = new double[参数个数];
		for (int i = 0; i < 参数个数; i++)
		{
			args[i] = 要求数值(参数列表.get(i), "函数 " + 函数名 + " 的第 " + (i + 1) + " 个参数");
		}

		switch (函数名)
		{
			case "sin":
				要求参数个数(函数名, 参数个数, 1);
				return Math.sin(args[0]);

			case "cos":
				要求参数个数(函数名, 参数个数, 1);
				return Math.cos(args[0]);

			case "tan":
				要求参数个数(函数名, 参数个数, 1);
				return Math.tan(args[0]);

			case "log":
				要求参数个数(函数名, 参数个数, 1);
				if (args[0] <= 0)
				{
					throw new SemanticException(
						"log 函数的参数必须为正数，当前值: " + args[0]);
				}
				return Math.log(args[0]);

			case "sqrt":
				要求参数个数(函数名, 参数个数, 1);
				if (args[0] < 0)
				{
					throw new SemanticException(
						"sqrt 函数的参数不能为负数，当前值: " + args[0]);
				}
				return Math.sqrt(args[0]);

			case "abs":
				要求参数个数(函数名, 参数个数, 1);
				return Math.abs(args[0]);

			case "pow":
				要求参数个数(函数名, 参数个数, 2);
				return Math.pow(args[0], args[1]);

			case "max":
				if (参数个数 < 2)
				{
					throw new MissingOperandException(
						"函数 max 需要至少 2 个参数，当前仅提供了 " + 参数个数 + " 个");
				}
				return 求最大值(args);

			case "min":
				if (参数个数 < 2)
				{
					throw new MissingOperandException(
						"函数 min 需要至少 2 个参数，当前仅提供了 " + 参数个数 + " 个");
				}
				return 求最小值(args);

			default:
				throw new FunctionCallException("未知函数: '" + 函数名 + "'");
		}
	}

	/**
	 * 检查参数个数是否符合预期，不符合则抛出异常。
	 *
	 * @param 函数名   函数名（用于错误消息）
	 * @param 实际个数 实际传入的参数个数
	 * @param 预期个数 预期参数个数
	 * @throws FunctionCallException 参数个数不匹配时抛出
	 */
	private void 要求参数个数(String 函数名, int 实际个数, int 预期个数)
		throws FunctionCallException
	{
		if (实际个数 != 预期个数)
		{
			throw new FunctionCallException(
				"函数 " + 函数名 + " 需要 " + 预期个数 + " 个参数，"
					+ "但提供了 " + 实际个数 + " 个");
		}
	}

	/**
	 * 求数组中的最大值。
	 */
	private double 求最大值(double[] args)
	{
		double max = args[0];
		for (int i = 1; i < args.length; i++)
		{
			if (args[i] > max)
			{
				max = args[i];
			}
		}
		return max;
	}

	/**
	 * 求数组中的最小值。
	 */
	private double 求最小值(double[] args)
	{
		double min = args[0];
		for (int i = 1; i < args.length; i++)
		{
			if (args[i] < min)
			{
				min = args[i];
			}
		}
		return min;
	}

	// ==================== 优先关系 ====================

	/**
	 * 返回算符的优先级数值。
	 * <p>
	 * 数值越大优先级越高。障碍符（{@code "("}、函数标记、{@code "#"}）返回
	 * {@link Integer#MAX_VALUE} 作为最高值，表示它们阻止一切正常归约。
	 *
	 * @param 算符 算符字符串标识
	 * @return 优先级数值
	 */
	private int 优先级(String 算符)
	{
		if (算符.equals("#"))
		{
			return 0;
		}
		if (算符.equals("?:"))
		{
			return 1;
		}
		if (算符.equals("?"))
		{
			return 2;
		}
		if (算符.equals("&") || 算符.equals("|"))
		{
			return 3;
		}
		if (算符.equals("!") || 算符.equals("~"))
		{
			return 4;
		}
		if (是关系算符(算符))
		{
			return 5;
		}
		if (算符.equals("+") || 算符.equals("-"))
		{
			return 6;
		}
		if (算符.equals("*") || 算符.equals("/"))
		{
			return 7;
		}
		if (算符.equals("^"))
		{
			return 8;
		}
		if (算符.equals("NEG"))
		{
			return 9;
		}
		// 障碍符
		if (算符.equals("(") || 算符.startsWith("FUNC:"))
		{
			return Integer.MAX_VALUE;
		}
		return -1; // 未知算符
	}

	/**
	 * 比较栈顶算符与输入算符的优先关系。
	 *
	 * @param 栈顶算符 算符栈顶的算符
	 * @param 输入算符 待移进的算符
	 * @return {@code '<'} 表示栈顶优先级更低（移进），{@code '>'} 表示栈顶优先级更高（归约）
	 */
	private char 比较优先级(String 栈顶算符, String 输入算符)
	{
		int 栈顶优先 = 优先级(栈顶算符);
		int 输入优先 = 优先级(输入算符);

		if (栈顶优先 < 输入优先)
		{
			return '<'; // 移进
		}
		if (栈顶优先 > 输入优先)
		{
			return '>'; // 归约
		}

		// 优先级相等时，根据结合性决定
		if (是右结合(输入算符))
		{
			return '<'; // 右结合：移进（如 ^, NEG）
		}
		else
		{
			return '>'; // 左结合：归约（如 +, -, *, /）
		}
	}

	/**
	 * 判断算符是否为右结合。
	 * <p>
	 * 右结合算符：{@code ^}（幂）、{@code NEG}（一元取负）、{@code ?}、{@code ?:}。
	 *
	 * @param 算符 算符字符串标识
	 * @return 是右结合返回 {@code true}
	 */
	private boolean 是右结合(String 算符)
	{
		return 算符.equals("^") || 算符.equals("NEG")
			|| 算符.equals("?") || 算符.equals("?:");
	}

	// ==================== 障碍符判断 ====================

	/**
	 * 判断算符栈顶元素是否为障碍符。
	 * <p>
	 * 障碍符（{@code "("}、函数标记、{@code "#"}）阻止正常的优先关系归约，
	 * 只有特定的 Token（{@code )}、{@code ,}、EOF）才能越过它们。
	 *
	 * @param 算符 算符字符串标识
	 * @return 是障碍符返回 {@code true}
	 */
	private boolean 是障碍符(String 算符)
	{
		return 算符.equals("(") || 算符.startsWith("FUNC:") || 算符.equals("#");
	}

	// ==================== 算符分类 ====================

	/**
	 * 判断是否为二元算符。
	 */
	private boolean 是二元算符(String 算符)
	{
		return 算符.equals("+") || 算符.equals("-")
			|| 算符.equals("*") || 算符.equals("/")
			|| 算符.equals("^")
			|| 算符.equals("&") || 算符.equals("|")
			|| 是关系算符(算符);
	}

	/**
	 * 判断是否为一元算符。
	 */
	private boolean 是一元算符(String 算符)
	{
		return 算符.equals("NEG") || 算符.equals("!") || 算符.equals("~");
	}

	/**
	 * 判断是否为算术运算符（{@code +, -, *, /, ^}）。
	 */
	private boolean 是算术算符(String 算符)
	{
		return 算符.equals("+") || 算符.equals("-")
			|| 算符.equals("*") || 算符.equals("/")
			|| 算符.equals("^");
	}

	/**
	 * 判断是否为关系运算符。
	 */
	private boolean 是关系算符(String 算符)
	{
		return 算符.equals("<") || 算符.equals(">")
			|| 算符.equals("<=") || 算符.equals(">=")
			|| 算符.equals("==") || 算符.equals("!=");
	}

	/**
	 * 判断是否为逻辑运算符（{@code &, |}）。
	 */
	private boolean 是逻辑算符(String 算符)
	{
		return 算符.equals("&") || 算符.equals("|");
	}

	/**
	 * 判断算符是否为合法的一元前缀算符。
	 * <p>
	 * 一元前缀算符 {@code !, ~, NEG} 可以合法地出现在操作数之前。
	 *
	 * @param 算符 算符字符串标识
	 * @return 是合法一元前缀返回 {@code true}
	 */
	private boolean 是合法一元前缀(String 算符)
	{
		return 算符.equals("!") || 算符.equals("~") || 算符.equals("NEG");
	}

	// ==================== 值栈操作 ====================

	/**
	 * 从值栈弹出一个操作数，若栈为空或弹出的是哨兵则报告错误。
	 *
	 * @param 描述 操作数用途描述（用于错误消息）
	 * @return 弹出的操作数（{@link Double} 或 {@link Boolean}）
	 * @throws MissingOperandException 若缺少操作数
	 */
	private Object 弹出操作数(String 描述) throws MissingOperandException
	{
		if (值栈.isEmpty())
		{
			throw new MissingOperandException("缺少操作数：" + 描述);
		}
		Object 值 = 值栈.pop();
		if (值 == 哨兵)
		{
			throw new MissingOperandException("缺少操作数：" + 描述 + "（遇到哨兵）");
		}
		return 值;
	}

	/**
	 * 要求值为数值类型（{@link Double}），否则抛出类型不匹配异常。
	 *
	 * @param 值    待检查的值
	 * @param 上下文 错误消息上下文
	 * @return 数值
	 * @throws TypeMismatchedException 若值为布尔类型
	 */
	private double 要求数值(Object 值, String 上下文) throws TypeMismatchedException
	{
		if (值 instanceof Double)
		{
			return ((Double) 值).doubleValue();
		}
		if (值 instanceof Boolean)
		{
			throw new TypeMismatchedException(
				"类型不匹配：" + 上下文 + " 需要数值类型，但得到布尔类型（true/false）");
		}
		throw new TypeMismatchedException(
			"类型不匹配：" + 上下文 + " 需要数值类型，但得到未知类型: " + 值.getClass().getSimpleName());
	}

	/**
	 * 要求值为布尔类型（{@link Boolean}），否则抛出类型不匹配异常。
	 *
	 * @param 值    待检查的值
	 * @param 上下文 错误消息上下文
	 * @return 布尔值
	 * @throws TypeMismatchedException 若值为数值类型
	 */
	private boolean 要求布尔(Object 值, String 上下文) throws TypeMismatchedException
	{
		if (值 instanceof Boolean)
		{
			return ((Boolean) 值).booleanValue();
		}
		if (值 instanceof Double)
		{
			throw new TypeMismatchedException(
				"类型不匹配：" + 上下文 + " 需要布尔类型（true/false），但得到数值类型");
		}
		throw new TypeMismatchedException(
			"类型不匹配：" + 上下文 + " 需要布尔类型，但得到未知类型: " + 值.getClass().getSimpleName());
	}

	/**
	 * 统计值栈中当前可用的操作数数量（跳过哨兵标记）。
	 * <p>
	 * 例如值栈为 [哨兵, 1.0, 哨兵, 2.0, 3.0]（栈顶在右），
	 * 则该方法从栈顶向下计数直到遇到哨兵为止，返回 2。
	 * </p>
	 *
	 * @return 当前顶层可用的操作数个数（不含哨兵）
	 */
	private int 计数操作数()
	{
		int 计数 = 0;
		for (int i = 值栈.size() - 1; i >= 0; i--)
		{
			if (值栈.get(i) == 哨兵)
			{
				break;
			}
			计数++;
		}
		return 计数;
	}

	/**
	 * 从值栈弹出一个哨兵标记。若栈顶不是哨兵则抛出异常。
	 *
	 * @param 上下文 错误消息上下文
	 * @throws SyntacticException 若栈顶不是哨兵
	 */
	private void 弹出哨兵(String 上下文) throws SyntacticException
	{
		if (值栈.isEmpty() || 值栈.peek() != 哨兵)
		{
			throw new SyntacticException(
				"内部错误：" + 上下文 + " 处期望哨兵标记但未找到——括号或函数参数结构异常");
		}
		值栈.pop();
	}
}
