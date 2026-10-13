/**
 * 缺少右括号时抛出的语法异常。
 * <p>
 * 当表达式扫描结束时仍有未配对的左括号 {@code (} 时触发。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class MissingRightParenthesisException extends SyntacticException
{
	/**
	 * 默认构造器。
	 */
	public MissingRightParenthesisException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public MissingRightParenthesisException(String msg)
	{
		super(msg);
	}
}
