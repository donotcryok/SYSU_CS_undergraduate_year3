/**
 * ExprEval 的词法分析器（扫描器），基于确定性有限状态自动机（DFA）实现。
 * <p>
 * 负责将输入的表达式字符串扫描为一串 {@link Token} 对象，供语法分析器（Parser）消费。
 * 本扫描器能够识别以下词法单元：
 * <ul>
 *   <li><b>数值常量</b>：整数、小数、科学记数法（如 {@code 1.2e-3}、{@code 2.25E+2}）</li>
 *   <li><b>布尔常量</b>：{@code true}、{@code false}</li>
 *   <li><b>预定义函数名</b>：{@code sin, cos, tan, log, sqrt, abs, pow, max, min}</li>
 *   <li><b>算术运算符</b>：{@code +, -, *, /, ^}</li>
 *   <li><b>关系运算符</b>：{@code <, >, <=, >=, ==, !=}</li>
 *   <li><b>逻辑/位运算符</b>：{@code &, |, ~, !}</li>
 *   <li><b>三元运算符</b>：{@code ?, :}</li>
 *   <li><b>分隔符</b>：{@code (, ), ,}</li>
 * </ul>
 * <p>
 * 特别注意：一元取负运算符与二元减法共用 {@code -} 字符，词法阶段统一标记为
 * {@code SUB}，具体的区分由语法分析器根据上下文（前驱 Token 类型）完成。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package parser;

import exceptions.*;

public class Scanner
{
	/** 输入的表达式字符串。 */
	private String expr;

	/** 当前扫描位置（0 起始）。 */
	private int pos;

	/** 表达式字符串的长度。 */
	private int len;

	/** 当前正在检查的字符，EOF 时为 {@code '\0'}。 */
	private char ch;

	/**
	 * 词法单元类型枚举。
	 * <p>
	 * 涵盖了 ExprEval 表达式计算器中所有可能的 Token 类别。
	 */
	public enum TokenType
	{
		/** 数值字面量（整数、小数、科学记数法）。 */
		NUMBER,
		/** 布尔字面量：{@code true} 或 {@code false}。 */
		BOOLEAN,
		/** 预定义函数标识符。 */
		IDENTIFIER,
		/** 加法运算符：{@code +}。 */
		PLUS,
		/** 减法/一元取负运算符：{@code -}。由语法阶段根据上下文区分语义。 */
		SUB,
		/** 乘法运算符：{@code *}。 */
		MUL,
		/** 除法运算符：{@code /}。 */
		DIV,
		/** 幂运算符：{@code ^}。 */
		POW,
		/** 逻辑与运算符：{@code &}。 */
		AND,
		/** 逻辑或运算符：{@code |}。 */
		OR,
		/** 逻辑非运算符：{@code !}。 */
		NOT,
		/** 按位取反运算符：{@code ~}。 */
		BIT_NOT,
		/** 小于运算符：{@code <}。 */
		LT,
		/** 大于运算符：{@code >}。 */
		GT,
		/** 小于等于运算符：{@code <=}。 */
		LE,
		/** 大于等于运算符：{@code >=}。 */
		GE,
		/** 等于运算符：{@code ==}。 */
		EQ,
		/** 不等于运算符：{@code !=}。 */
		NE,
		/** 三元条件运算符：{@code ?}。 */
		QUEST,
		/** 三元分支运算符：{@code :}。 */
		COLON,
		/** 左括号：{@code (}。 */
		LPAREN,
		/** 右括号：{@code )}。 */
		RPAREN,
		/** 逗号分隔符：{@code ,}。 */
		COMMA,
		/** 输入结束标记。 */
		EOF
	}

	/**
	 * 表示一个词法单元，包含类型、词素文本以及可选的数值/布尔值。
	 */
	public static class Token
	{
		/** 本 Token 的类型。 */
		public final TokenType type;

		/** 本 Token 对应的原始文本（词素）。 */
		public final String lexeme;

		/** 数值类型的 Token 对应的 double 值；非数值 Token 为 0.0。 */
		public final double numValue;

		/** 布尔类型的 Token 对应的 boolean 值；非布尔 Token 为 false。 */
		public final boolean boolValue;

		/**
		 * 为非数值/非布尔类型的 Token 构造实例（运算符、分隔符、标识符、EOF等）。
		 *
		 * @param type   Token 类型
		 * @param lexeme 匹配的原始文本
		 */
		public Token(TokenType type, String lexeme)
		{
			this.type = type;
			this.lexeme = lexeme;
			this.numValue = 0.0;
			this.boolValue = false;
		}

		/**
		 * 为数值常量构造 Token 实例。
		 *
		 * @param type     Token 类型（必须为 NUMBER）
		 * @param lexeme   匹配的原始文本
		 * @param numValue 解析后的数值
		 */
		public Token(TokenType type, String lexeme, double numValue)
		{
			this.type = type;
			this.lexeme = lexeme;
			this.numValue = numValue;
			this.boolValue = false;
		}

		/**
		 * 为布尔常量构造 Token 实例。
		 *
		 * @param type      Token 类型（必须为 BOOLEAN）
		 * @param lexeme   匹配的原始文本
		 * @param boolValue 解析后的布尔值
		 */
		public Token(TokenType type, String lexeme, boolean boolValue)
		{
			this.type = type;
			this.lexeme = lexeme;
			this.numValue = 0.0;
			this.boolValue = boolValue;
		}

		/**
		 * 返回本 Token 的可读字符串表示。
		 *
		 * @return 形如 {@code "NUMBER<3.14>"} 或 {@code "PLUS"} 的字符串
		 */
		public String toString()
		{
			switch (type)
			{
				case NUMBER:
					return "NUMBER<" + lexeme + ">";
				case BOOLEAN:
					return "BOOLEAN<" + lexeme + ">";
				case IDENTIFIER:
					return "IDENTIFIER<" + lexeme + ">";
				case EOF:
					return "EOF";
				default:
					return type.name();
			}
		}
	}

	/** 当前前瞻 Token（已扫描但尚未消费）。 */
	private Token currentToken;

	/**
	 * 为给定的表达式字符串构造 Scanner，并立即扫描第一个 Token 作为前瞻。
	 *
	 * @param expression 待词法分析的表达式字符串
	 * @throws LexicalException 若初始扫描过程中发现词法错误
	 */
	public Scanner(String expression) throws LexicalException
	{
		this.expr = expression;
		this.pos = 0;
		this.len = expression.length();
		advanceChar();
		currentToken = nextToken();
	}

	// ==================== 公开 API ====================

	/**
	 * 返回当前前瞻 Token，但不消费它。
	 *
	 * @return 当前 Token
	 */
	public Token peek()
	{
		return currentToken;
	}

	/**
	 * 消费当前 Token 并返回它，然后扫描下一个 Token 作为新的前瞻。
	 *
	 * @return 被消费的前一个前瞻 Token
	 * @throws LexicalException 若向前扫描时发现词法错误
	 */
	public Token advance() throws LexicalException
	{
		Token t = currentToken;
		currentToken = nextToken();
		return t;
	}

	// ==================== 字符级基本操作 ====================

	/**
	 * 从输入中读取下一个字符到 {@code ch}。到达输入末尾时将 {@code ch} 设为 {@code '\0'}。
	 */
	private void advanceChar()
	{
		if (pos < len)
		{
			ch = expr.charAt(pos);
			pos++;
		}
		else
		{
			ch = '\0';
		}
	}

	/**
	 * 跳过所有空白字符（空格和制表符）。
	 */
	private void skipWhitespace()
	{
		while (ch == ' ' || ch == '\t')
		{
			advanceChar();
		}
	}

	// ==================== DFA：Token 扫描主控 ====================

	/**
	 * 使用 DFA 模型从输入中扫描下一个 Token。
	 * <p>
	 * 根据当前字符的类型分发到不同的子 DFA：
	 * <ul>
	 *   <li>数字开头 → {@link #scanNumber()} （数值 DFA）</li>
	 *   <li>字母/下划线开头 → {@link #scanIdentifierOrKeyword()} （标识符 DFA）</li>
	 *   <li>其他符号 → 单字符/双字符运算符或分隔符</li>
	 * </ul>
	 *
	 * @return 扫描到的下一个 Token
	 * @throws LexicalException 遇到非法字符或数值格式错误时抛出
	 */
	private Token nextToken() throws LexicalException
	{
		skipWhitespace();

		if (ch == '\0')
		{
			return new Token(TokenType.EOF, "");
		}

		// ---- 数字：启动数值 DFA ----
		if (ch >= '0' && ch <= '9')
		{
			return scanNumber();
		}

		// ---- 字母/下划线：启动标识符/关键字 DFA ----
		if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || ch == '_')
		{
			return scanIdentifierOrKeyword();
		}

		// ---- 单字符/双字符运算符及分隔符 ----
		switch (ch)
		{
			case '+':
				advanceChar();
				return new Token(TokenType.PLUS, "+");
			case '-':
				advanceChar();
				// 词法阶段不区分一元取负与二元减法，统一标记为 SUB
				return new Token(TokenType.SUB, "-");
			case '*':
				advanceChar();
				return new Token(TokenType.MUL, "*");
			case '/':
				advanceChar();
				return new Token(TokenType.DIV, "/");
			case '^':
				advanceChar();
				return new Token(TokenType.POW, "^");
			case '&':
				advanceChar();
				return new Token(TokenType.AND, "&");
			case '|':
				advanceChar();
				return new Token(TokenType.OR, "|");
			case '~':
				advanceChar();
				return new Token(TokenType.BIT_NOT, "~");
			case '!':
				advanceChar();
				if (ch == '=')
				{
					advanceChar();
					return new Token(TokenType.NE, "!=");
				}
				return new Token(TokenType.NOT, "!");
			case '<':
				advanceChar();
				if (ch == '=')
				{
					advanceChar();
					return new Token(TokenType.LE, "<=");
				}
				return new Token(TokenType.LT, "<");
			case '>':
				advanceChar();
				if (ch == '=')
				{
					advanceChar();
					return new Token(TokenType.GE, ">=");
				}
				return new Token(TokenType.GT, ">");
			case '=':
				advanceChar();
				if (ch == '=')
				{
					advanceChar();
					return new Token(TokenType.EQ, "==");
				}
				// 孤立的 '=' 在 ExprEval 中是非法的
				throw new IllegalSymbolException("非法符号: '=' （是否想输入 '=='？）");
			case '?':
				advanceChar();
				return new Token(TokenType.QUEST, "?");
			case ':':
				advanceChar();
				return new Token(TokenType.COLON, ":");
			case '(':
				advanceChar();
				return new Token(TokenType.LPAREN, "(");
			case ')':
				advanceChar();
				return new Token(TokenType.RPAREN, ")");
			case ',':
				advanceChar();
				return new Token(TokenType.COMMA, ",");
			default:
				throw new IllegalSymbolException("无法识别的符号: '" + ch + "'");
		}
	}

	// ==================== DFA：数值扫描 ====================

	/**
	 * 数值扫描 DFA 的状态枚举。
	 * <p>
	 * 状态转换图：
	 * <pre>
	 * INT_PART --[.]--> DOT --[digit]--> FRAC_PART
	 * INT_PART --[e/E]--> EXP_MARK
	 * FRAC_PART --[e/E]--> EXP_MARK
	 * EXP_MARK --[+/-]--> EXP_SIGN --[digit]--> EXP_DIGITS
	 * EXP_MARK --[digit]--> EXP_DIGITS
	 * </pre>
	 */
	private enum NumberState
	{
		/** 初始状态：扫描整数部分。 */
		INT_PART,
		/** 遇到小数点后，必须跟随至少一位数字。 */
		DOT,
		/** 扫描小数部分。 */
		FRAC_PART,
		/** 遇到 'e' 或 'E' 后，等待符号或指数数字。 */
		EXP_MARK,
		/** 遇到指数符号后，必须跟随至少一位数字。 */
		EXP_SIGN,
		/** 扫描指数数字部分。 */
		EXP_DIGITS
	}

	/**
	 * 数值常量 DFA 实现。
	 * <p>
	 * 可以识别以下格式：
	 * <ul>
	 *   <li><b>整数</b>：{@code 42}、{@code 0}</li>
	 *   <li><b>小数</b>：{@code 3.14}、{@code .5}</li>
	 *   <li><b>科学记数法</b>：{@code 1.2e-3}、{@code 2E+2}、{@code 130e-1}</li>
	 * </ul>
	 * <p>
	 * <b>非法格式示例</b>：{@code 10.E+5} —— 小数点后无数字，将抛出异常。
	 *
	 * @return 类型为 NUMBER 的 Token
	 * @throws IllegalDecimalException 数值格式非法时抛出
	 */
	private Token scanNumber() throws IllegalDecimalException
	{
		StringBuilder sb = new StringBuilder();
		NumberState state = NumberState.INT_PART;

		while (true)
		{
			switch (state)
			{
				case INT_PART:
					// 持续累积整数部分数字
					if (ch >= '0' && ch <= '9')
					{
						sb.append(ch);
						advanceChar();
					}
					else if (ch == '.')
					{
						// 遇到小数点，转入 DOT 状态等待小数数字
						sb.append(ch);
						advanceChar();
						state = NumberState.DOT;
					}
					else if (ch == 'e' || ch == 'E')
					{
						// 整数后直接跟指数标记
						sb.append(ch);
						advanceChar();
						state = NumberState.EXP_MARK;
					}
					else
					{
						// 整数常量结束
						return new Token(TokenType.NUMBER, sb.toString(),
							Double.parseDouble(sb.toString()));
					}
					break;

				case DOT:
					// 小数点后必须至少有一位数字，否则为非法小数
					if (ch >= '0' && ch <= '9')
					{
						sb.append(ch);
						advanceChar();
						state = NumberState.FRAC_PART;
					}
					else
					{
						throw new IllegalDecimalException(
							"非法小数常量: '" + sb.toString()
								+ ch + "' —— 小数点后缺少数字");
					}
					break;

				case FRAC_PART:
					// 持续累积小数数字
					if (ch >= '0' && ch <= '9')
					{
						sb.append(ch);
						advanceChar();
					}
					else if (ch == 'e' || ch == 'E')
					{
						// 小数后跟指数标记
						sb.append(ch);
						advanceChar();
						state = NumberState.EXP_MARK;
					}
					else
					{
						// 小数常量结束
						return new Token(TokenType.NUMBER, sb.toString(),
							Double.parseDouble(sb.toString()));
					}
					break;

				case EXP_MARK:
					// 指数标记后可跟 +、- 或直接跟数字
					if (ch == '+' || ch == '-')
					{
						sb.append(ch);
						advanceChar();
						state = NumberState.EXP_SIGN;
					}
					else if (ch >= '0' && ch <= '9')
					{
						sb.append(ch);
						advanceChar();
						state = NumberState.EXP_DIGITS;
					}
					else
					{
						throw new IllegalDecimalException(
							"非法科学记数法: '" + sb.toString()
								+ ch + "' —— 缺少指数数字");
					}
					break;

				case EXP_SIGN:
					// 指数符号后必须至少有一位数字
					if (ch >= '0' && ch <= '9')
					{
						sb.append(ch);
						advanceChar();
						state = NumberState.EXP_DIGITS;
					}
					else
					{
						throw new IllegalDecimalException(
							"非法科学记数法: '" + sb.toString()
								+ ch + "' —— 符号后缺少指数数字");
					}
					break;

				case EXP_DIGITS:
					// 持续累积指数数字
					if (ch >= '0' && ch <= '9')
					{
						sb.append(ch);
						advanceChar();
					}
					else
					{
						// 科学记数法常量结束
						return new Token(TokenType.NUMBER, sb.toString(),
							Double.parseDouble(sb.toString()));
					}
					break;
			}
		}
	}

	// ==================== DFA：标识符/关键字扫描 ====================

	/**
	 * ExprEval 中预定义的函数名集合。
	 * <p>
	 * 匹配时忽略大小写（统一转为小写比较）。
	 */
	private static final java.util.Set<String> 预定义函数集合;

	static
	{
		预定义函数集合 = new java.util.HashSet<String>();
		预定义函数集合.add("sin");
		预定义函数集合.add("cos");
		预定义函数集合.add("tan");
		预定义函数集合.add("log");
		预定义函数集合.add("sqrt");
		预定义函数集合.add("abs");
		预定义函数集合.add("pow");
		预定义函数集合.add("max");
		预定义函数集合.add("min");
	}

	/**
	 * 标识符/关键字 DFA 实现。
	 * <p>
	 * 识别规则：
	 * <ol>
	 *   <li>扫描完完整标识符后，转为小写进行查表分类：</li>
	 *   <li>{@code true} / {@code false} → {@code TokenType.BOOLEAN}</li>
	 *   <li>位于预定义函数集合中 → {@code TokenType.IDENTIFIER}</li>
	 *   <li>其他 → 抛出 {@link IllegalIdentifierException}</li>
	 * </ol>
	 *
	 * @return 类型为 BOOLEAN 或 IDENTIFIER 的 Token
	 * @throws IllegalIdentifierException 标识符不在已知关键字/函数集合中时抛出
	 */
	private Token scanIdentifierOrKeyword() throws IllegalIdentifierException
	{
		StringBuilder sb = new StringBuilder();

		// 累积所有字母、数字和下划线字符
		while ((ch >= 'a' && ch <= 'z')
			|| (ch >= 'A' && ch <= 'Z')
			|| (ch >= '0' && ch <= '9')
			|| ch == '_')
		{
			sb.append(ch);
			advanceChar();
		}

		String word = sb.toString();
		String lower = word.toLowerCase();

		// 检查布尔常量
		if (lower.equals("true"))
		{
			return new Token(TokenType.BOOLEAN, word, true);
		}
		if (lower.equals("false"))
		{
			return new Token(TokenType.BOOLEAN, word, false);
		}

		// 检查预定义函数名
		if (预定义函数集合.contains(lower))
		{
			return new Token(TokenType.IDENTIFIER, lower);
		}

		// 未知标识符 → 非法
		throw new IllegalIdentifierException(
			"未识别的标识符: '" + word
				+ "' —— 不是布尔常量，也不是预定义函数名");
	}
}
