/**
 * 缺少左括号时抛出的语法异常。
 * <p>
 * 当扫描到孤立的右括号 {@code )} 而没有与之匹配的左括号时触发。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class MissingLeftParenthesisException extends SyntacticException
{
	/**
	 * 默认构造器。
	 */
	public MissingLeftParenthesisException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public MissingLeftParenthesisException(String msg)
	{
		super(msg);
	}
}
