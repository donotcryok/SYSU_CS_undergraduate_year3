import java.io.FileReader;

/**
 * 词法分析器测试入口 —— 读取 Oberon-0 源文件，逐 Token 输出。
 *
 * <p>用法: {@code java OberonScannerTest <源文件路径>}
 */
public class OberonScannerTest {
    /**
     * 主入口.
     *
     * @param args 命令行参数: args[0] = Oberon-0 源文件路径
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("用法: java OberonScannerTest <Oberon-0源文件路径>");
            System.err.println("示例: java OberonScannerTest ..\\ex1\\testcases\\StudentStats.obr");
            System.exit(1);
        }

        String filename = args[0];
        try {
            OberonScanner scanner = new OberonScanner(new FileReader(filename));
            Token t;
            int count = 0;
            while ((t = scanner.yylex()) != null) {
                System.out.println(t);
                count++;
            }
            System.out.println();
            System.out.println("扫描完成: " + count + " 个 Token");
        } catch (Exception e) {
            System.err.println("[错误] " + e.getClass().getSimpleName());
            System.err.println("  " + e.getMessage());
            System.exit(1);
        }
    }
}
