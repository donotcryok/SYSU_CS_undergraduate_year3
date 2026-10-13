/**
 * 词法分析中遇到未知标识符时抛出。
 * <p>
 * 标识符不能仅为字母数字下划线组合，还必须是布尔常量（{@code true} / {@code false}）
 * 或者预定义函数名（如 {@code sin}、{@code max} 等）。
 * 任何不属于上述两类的标识符将触发此异常。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class IllegalIdentifierException extends LexicalException
{
	/**
	 * 默认构造器。
	 */
	public IllegalIdentifierException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public IllegalIdentifierException(String msg)
	{
		super(msg);
	}
}
