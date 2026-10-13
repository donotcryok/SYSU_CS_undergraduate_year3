/**
 * 表达式为空时抛出的语法异常。
 * <p>
 * ExprEval 不允许计算空字符串，必须在输入框内输入合法的表达式。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class EmptyExpressionException extends SyntacticException
{
	/**
	 * 默认构造器。
	 */
	public EmptyExpressionException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public EmptyExpressionException(String msg)
	{
		super(msg);
	}
}
