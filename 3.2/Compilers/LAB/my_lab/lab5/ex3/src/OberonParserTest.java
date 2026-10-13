import java.io.*;
import callgraph.*;

/**
 * OberonParserTest —— 实验三 LALR 语法分析器测试驱动.
 *
 * <p>用法: {@code java OberonParserTest <Oberon-0源文件路径>}
 *
 * <p>流程:
 * <ol>
 *   <li>创建 CallGraph 实例</li>
 *   <li>用 CupScanner 读取源文件, 交给 Parser 做 LALR 语法分析</li>
 *   <li>分析成功后显示 CallGraph 调用图</li>
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
        System.out.println("  ROSE 实验三 —— Oberon-0 语法分析");
        System.out.println("  源文件: " + filename);
        System.out.println("========================================");
        System.out.println();

        try {
            /* 1. 创建 CallGraph */
            CallGraph graph = new CallGraph();

            /* 2. 创建词法扫描器 → 桥接为 CUP Scanner */
            CupScanner scanner = new CupScanner(new FileReader(filename));

            /* 3. 创建 Parser 并解析 */
            Parser parser = new Parser(graph, scanner);

            System.out.println("[语法分析] 开始解析...");
            parser.parse();

            System.out.println();
            System.out.println("=== 语法分析通过, 无语法错误! ===");
            System.out.println();

            /* 4. 显示调用图 */
            System.out.println("[调用图] 显示中...");
            graph.show();

        } catch (Exception e) {
            System.err.println();
            System.err.println("=== 语法分析失败 ===");
            System.err.println("[异常] " + e.getClass().getName());
            System.err.println("  " + e.getMessage());

            /* 打印词法错误明细 */
            Throwable cause = e.getCause();
            while (cause != null) {
                System.err.println("  原因: " + cause.getClass().getName() + " - " + cause.getMessage());
                cause = cause.getCause();
            }
            System.exit(1);
        }
    }
}
