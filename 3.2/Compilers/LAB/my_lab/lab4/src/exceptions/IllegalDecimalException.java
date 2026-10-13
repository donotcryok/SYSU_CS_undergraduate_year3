/**
 * 词法分析中发现格式错误的小数常量时抛出。
 * <p>
 * 典型触发场景：小数点后缺少数字（如 {@code 10.E+5}）、
 * 科学记数法指数部分格式错误（如 {@code 1.2e}）。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class IllegalDecimalException extends LexicalException
{
	/**
	 * 默认构造器。
	 */
	public IllegalDecimalException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public IllegalDecimalException(String msg)
	{
		super(msg);
	}
}
