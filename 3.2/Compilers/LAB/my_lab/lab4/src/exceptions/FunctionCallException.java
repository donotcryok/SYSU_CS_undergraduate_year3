/**
 * 函数调用语法错误时抛出的异常。
 * <p>
 * 触发条件包括：
 * <ul>
 *   <li>参数数量不匹配（如 {@code sin(2, 1)}）</li>
 *   <li>参数数量过少（如 {@code min(2.5)}）</li>
 * </ul>
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class FunctionCallException extends SyntacticException
{
	/**
	 * 默认构造器。
	 */
	public FunctionCallException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public FunctionCallException(String msg)
	{
		super(msg);
	}
}
