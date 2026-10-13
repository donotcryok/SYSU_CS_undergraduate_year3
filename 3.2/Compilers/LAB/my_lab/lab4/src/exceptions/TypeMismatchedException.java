/**
 * 类型不匹配异常，属于语义错误。
 * <p>
 * 当运算符的操作数类型不兼容时抛出。例如：
 * <ul>
 *   <li>布尔值与数值进行算术运算（如 {@code true + 3}）</li>
 *   <li>数值参数被传入需要布尔参数的位置</li>
 * </ul>
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class TypeMismatchedException extends SemanticException
{
	/**
	 * 默认构造器。
	 */
	public TypeMismatchedException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public TypeMismatchedException(String msg)
	{
		super(msg);
	}
}
