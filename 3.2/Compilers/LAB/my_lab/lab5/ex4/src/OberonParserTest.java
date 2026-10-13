import java.io.*;
import flowchart.*;

/**
 * OberonParserTest —— 实验四 递归下降解析器测试驱动.
 *
 * <p>用法: {@code java OberonParserTest <Oberon-0源文件路径>}
 *
 * <p>流程:
 * <ol>
 *   <li>创建 OberonParser 实例</li>
 *   <li>调用 parseModule() 进行递归下降语法分析</li>
 *   <li>分析成功后调用 module.show() 显示 Flowchart 流程图</li>
 *   <li>分析失败则打印语法错误信息</li>
 * </ol>
 */
public class OberonParserTest {

    /**
     * 主入口.
     *
     * @param args 命令行参数: args[0] = Oberon-0 源文件路径
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("用法: java OberonParserTest <Oberon-0源文件路径>");
            System.err.println("示例: java OberonParserTest ..\\ex1\\testcases\\StudentStats.obr");
            System.exit(1);
        }

        String filename = args[0];
        System.out.println("========================================");
        System.out.println("  ROSE 实验四 —— 递归下降语法分析");
        System.out.println("  源文件: " + filename);
        System.out.println("========================================");
        System.out.println();

        try {
            OberonParser parser = new OberonParser(new FileReader(filename));

            System.out.println("[语法分析] 开始递归下降解析...");
            flowchart.Module module = parser.parseModule();

            System.out.println();
            System.out.println("=== 递归下降语法分析通过! ===");
            System.out.println();

            // 显示流程图
            System.out.println("[流程图] 显示中...");
            module.show();

        } catch (Exception e) {
            System.err.println();
            System.err.println("=== 语法分析失败 ===");
            System.err.println("[异常] " + e.getClass().getName());
            System.err.println("  " + e.getMessage());
            System.exit(1);
        }
    }
}
