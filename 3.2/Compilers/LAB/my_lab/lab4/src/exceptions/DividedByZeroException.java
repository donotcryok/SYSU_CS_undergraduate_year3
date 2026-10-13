/**
 * 除零异常，属于语义错误。
 * <p>
 * 当执行除法或取模运算时除数为零时抛出。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class DividedByZeroException extends SemanticException
{
	/**
	 * 默认构造器。
	 */
	public DividedByZeroException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public DividedByZeroException(String msg)
	{
		super(msg);
	}
}
