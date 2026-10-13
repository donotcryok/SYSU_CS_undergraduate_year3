/**
 * 缺少运算符时抛出的语法异常。
 * <p>
 * 当两个操作数之间缺少必要的运算符时触发。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class MissingOperatorException extends SyntacticException
{
	/**
	 * 默认构造器。
	 */
	public MissingOperatorException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public MissingOperatorException(String msg)
	{
		super(msg);
	}
}
