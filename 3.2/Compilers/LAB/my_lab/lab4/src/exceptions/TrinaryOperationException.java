/**
 * 三元运算符（{@code ? :}）语法错误时抛出的异常。
 * <p>
 * 触发条件包括但不限于：
 * <ul>
 *   <li>{@code ?} 和 {@code :} 不配对</li>
 *   <li>条件表达式的类型不是布尔型</li>
 *   <li>缺少某个分支表达式</li>
 * </ul>
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class TrinaryOperationException extends SyntacticException
{
	/**
	 * 默认构造器。
	 */
	public TrinaryOperationException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public TrinaryOperationException(String msg)
	{
		super(msg);
	}
}
