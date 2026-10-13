/**
 * 缺少操作数时抛出的语法异常。
 * <p>
 * 当算符优先分析的归约过程中发现运算符缺少所需的操作数时触发。
 * 例如：二元运算符只有左操作数而缺少右操作数。
 *
 * @author 马福泉
 * @date 2026年5月10日
 * @version 1.0
 */
package exceptions;

public class MissingOperandException extends SyntacticException
{
	/**
	 * 默认构造器。
	 */
	public MissingOperandException()
	{
		super();
	}

	/**
	 * 携带详细错误信息的构造器。
	 *
	 * @param msg 错误详细信息
	 */
	public MissingOperandException(String msg)
	{
		super(msg);
	}
}
