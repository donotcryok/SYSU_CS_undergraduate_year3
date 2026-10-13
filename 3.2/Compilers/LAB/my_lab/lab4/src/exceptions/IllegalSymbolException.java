/**
 * 词法分析中遇到无法识别的符号字符时抛出。
 * <p>
 * ExprEval 仅支持有限的符号集；任何不在合法字符集中的字符
 * （如 {@code @}、{@code #}、{@code $} 等）都将触发此异常。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class IllegalSymbolException extends LexicalException
{
	/**
	 * 默认构造器。
	 */
	public IllegalSymbolException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public IllegalSymbolException(String msg)
	{
		super(msg);
	}
}
