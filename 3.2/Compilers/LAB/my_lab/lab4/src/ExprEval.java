/**
 * ExprEval 表达式计算器的 GUI 启动入口。
 * <p>
 * 本类仅负责启动图形用户界面（{@link gui.MainWindow}），
 * 不包含任何业务逻辑。
 * </p>
 *
 * @author 马福泉
 * @version 1.0
 */
public class ExprEval
{
	/**
	 * 应用程序入口。
	 *
	 * @param args 命令行参数（未使用）
	 */
	public static void main(String[] args)
	{
		new gui.MainWindow().show();
	}
}
