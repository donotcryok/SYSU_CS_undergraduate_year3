/**
 * 语义分析阶段所有异常的根类。
 * <p>
 * 子类包括类型不兼容（{@link TypeMismatchedException}）
 * 以及除零错误（{@link DividedByZeroException}）。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class SemanticException extends ExpressionException
{
	/**
	 * 默认构造器。
	 */
	public SemanticException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public SemanticException(String msg)
	{
		super(msg);
	}
}
