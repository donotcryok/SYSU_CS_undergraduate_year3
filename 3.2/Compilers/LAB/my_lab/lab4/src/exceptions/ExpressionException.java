/**
 * ExprEval 表达式计算器所有异常的根类。
 * <p>
 * 该异常体系分为三大分支：
 * <ul>
 *   <li>{@link LexicalException}  —— 词法分析阶段异常</li>
 *   <li>{@link SyntacticException} —— 语法分析阶段异常</li>
 *   <li>{@link SemanticException}  —— 语义分析阶段异常</li>
 * </ul>
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class ExpressionException extends Exception
{
	/**
	 * 默认构造器。
	 */
	public ExpressionException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public ExpressionException(String msg)
	{
		super(msg);
	}
}
