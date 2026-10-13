/**
 * 语法分析阶段所有异常的根类。
 * <p>
 * 子类涵盖了所有在算符优先分析过程中可能发现的结构性错误。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class SyntacticException extends ExpressionException
{
	/**
	 * 默认构造器。
	 */
	public SyntacticException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public SyntacticException(String msg)
	{
		super(msg);
	}
}
