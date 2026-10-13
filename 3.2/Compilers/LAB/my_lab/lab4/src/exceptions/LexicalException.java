/**
 * 词法分析阶段所有异常的根类。
 * <p>
 * 子类包括：
 * <ul>
 *   <li>{@link IllegalDecimalException}    —— 非法的小数常量</li>
 *   <li>{@link IllegalIdentifierException} —— 非法的标识符</li>
 *   <li>{@link IllegalSymbolException}     —— 非法的符号字符</li>
 * </ul>
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class LexicalException extends ExpressionException
{
	/**
	 * 默认构造器。
	 */
	public LexicalException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public LexicalException(String msg)
	{
		super(msg);
	}
}
