import java.io.*;
import java.util.*;

/**
 * 性能测试类 - 对比尾递归版本与循环版本的性能差异
 * 
 * <p>本测试类用于验证消除尾递归对程序性能的影响：
 * <ul>
 *   <li>生成不同长度的合法中缀表达式（10^2, 10^3, 10^4, 10^5 字符）</li>
 *   <li>分别测试递归版本和循环版本的执行时间</li>
 *   <li>输出 CSV 格式数据到控制台和文件</li>
 *   <li>自动保存结果到 data/perf_results.csv</li>
 * </ul>
 * 
 * <h2>测试方法</h2>
 * <pre>
 * java PerformanceTest
 * </pre>
 * 
 * <h2>输出文件</h2>
 * <pre>
 * data/perf_results.csv - CSV格式的性能数据
 * </pre>
 * 
 * @author 编译原理实验
 * @version 2.1
 * @since 2024
 */
public class PerformanceTest {
    
    /** 测试的表达式长度数组 */
    private static final int[] TEST_LENGTHS = {100, 500, 1000, 2000, 5000, 10000, 20000, 50000};
    
    /** 每个长度测试的次数（取平均值） */
    private static final int ITERATIONS = 5;
    
    /** 随机数生成器 */
    private static final Random random = new Random(42); // 固定种子保证可重复性
    
    /** CSV 输出文件路径 */
    private static final String CSV_FILE_PATH = "data/perf_results.csv";
    
    /** 性能结果记录类 */
    static class PerfResult {
        int length;
        long recursiveTime;
        long iterativeTime;
        int stackDepth;
        boolean stackOverflow;
        double speedup;
        
        PerfResult(int length, long recursiveTime, long iterativeTime, int stackDepth, boolean stackOverflow) {
            this.length = length;
            this.recursiveTime = recursiveTime;
            this.iterativeTime = iterativeTime;
            this.stackDepth = stackDepth;
            this.stackOverflow = stackOverflow;
            this.speedup = (recursiveTime > 0 && !stackOverflow) ? 
                (double) recursiveTime / Math.max(iterativeTime, 1) : 0;
        }
        
        /** 转换为 CSV 行 */
        String toCSVRow() {
            // 如果发生栈溢出，递归时间记录为 NaN
            String recTimeStr = stackOverflow ? "NaN" : String.valueOf(recursiveTime);
            String speedupStr = stackOverflow ? "NaN" : String.format("%.2f", speedup);
            return String.format("%d,%s,%d,%d,%s", 
                length, recTimeStr, iterativeTime, stackDepth, speedupStr);
        }
    }
    
    /**
     * 生成指定长度的合法中缀表达式
     * 
     * <p>生成的表达式格式为: d+d-d+d-d+... 其中 d 为随机数字
     * 
     * @param length 目标长度（字符数）
     * @return 生成的中缀表达式字符串
     */
    public static String generateInfixExpression(int length) {
        StringBuilder sb = new StringBuilder(length);
        
        // 第一个数字
        sb.append(random.nextInt(10));
        
        // 交替添加运算符和数字
        while (sb.length() < length - 1) {
            char op = random.nextBoolean() ? '+' : '-';
            sb.append(op);
            sb.append(random.nextInt(10));
        }
        
        return sb.toString();
    }
    
    /**
     * 递归版本的 Parser（用于性能对比）
     * 
     * <p>保留原始的尾递归实现，用于与循环版本对比性能。
     */
    static class RecursiveParser {
        private int lookahead;
        private int position;
        private PushbackReader reader;
        private int maxStackDepth;
        private int currentStackDepth;
        
        public RecursiveParser(InputStream inputStream) throws IOException {
            this.reader = new PushbackReader(new InputStreamReader(inputStream), 2);
            this.lookahead = -1;
            this.position = 0;
            this.maxStackDepth = 0;
            this.currentStackDepth = 0;
            advance();
        }
        
        private void advance() throws IOException {
            lookahead = reader.read();
            if (lookahead != -1) {
                position++;
            }
        }
        
        public void expr() throws IOException {
            term();
            rest();
        }
        
        /**
         * 递归版本的 rest() 方法
         * 
         * <p>这是原始的尾递归实现，用于性能对比。
         * 注意：对于超长表达式可能导致栈溢出。
         */
        void rest() throws IOException {
            currentStackDepth++;
            if (currentStackDepth > maxStackDepth) {
                maxStackDepth = currentStackDepth;
            }
            
            if (lookahead == '+') {
                match('+');
                term();
                System.out.write('+');
                rest();
            } else if (lookahead == '-') {
                match('-');
                term();
                System.out.write('-');
                rest();
            }
            
            currentStackDepth--;
        }
        
        void term() throws IOException {
            if (Character.isDigit((char) lookahead)) {
                System.out.write((char) lookahead);
                match(lookahead);
            }
        }
        
        void match(int t) throws IOException {
            if (lookahead == t) {
                advance();
            }
        }
        
        public int getMaxStackDepth() {
            return maxStackDepth;
        }
    }
    
    /**
     * 测试递归版本的性能
     * 
     * @param expression 输入表达式
     * @return 包含执行时间(ms)和最大栈深度的数组，如果栈溢出返回 null
     */
    public static long[] testRecursive(String expression) {
        try {
            // 使用 ByteArrayOutputStream 捕获输出
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            PrintStream ps = new PrintStream(baos);
            PrintStream originalOut = System.out;
            System.setOut(ps);
            
            long startTime = System.nanoTime();
            
            RecursiveParser parser = new RecursiveParser(
                new ByteArrayInputStream(expression.getBytes())
            );
            parser.expr();
            
            long endTime = System.nanoTime();
            
            System.setOut(originalOut);
            
            long timeMs = (endTime - startTime) / 1_000_000; // 转换为毫秒
            int maxDepth = parser.getMaxStackDepth();
            
            return new long[]{timeMs, maxDepth};
        } catch (StackOverflowError e) {
            // 栈溢出，返回 null 表示失败
            System.setOut(System.out); // 恢复标准输出
            return null;
        } catch (IOException e) {
            System.setOut(System.out);
            return null;
        }
    }
    
    /**
     * 测试循环版本（重构后）的性能
     * 
     * @param expression 输入表达式
     * @return 执行时间(ms)
     */
    public static long testIterative(String expression) throws IOException {
        // 使用 ByteArrayOutputStream 捕获输出
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        PrintStream ps = new PrintStream(baos);
        PrintStream originalOut = System.out;
        System.setOut(ps);
        
        long startTime = System.nanoTime();
        
        Parser parser = new Parser(
            new ByteArrayInputStream(expression.getBytes())
        );
        parser.expr();
        
        long endTime = System.nanoTime();
        
        System.setOut(originalOut);
        
        return (endTime - startTime) / 1_000_000; // 转换为毫秒
    }
    
    /**
     * 运行性能测试并收集结果
     * 
     * @return 性能结果列表
     */
    public static List<PerfResult> runPerformanceTest() {
        List<PerfResult> results = new ArrayList<>();
        
        System.out.println("========================================");
        System.out.println("  尾递归消除性能对比测试");
        System.out.println("========================================");
        System.out.println();
        System.out.println("测试次数: " + ITERATIONS + " 次/长度");
        System.out.println();
        
        // CSV 表头 - 控制台输出
        System.out.println("ExpressionLength,RecursiveTime_ms,IterativeTime_ms,StackDepth,Speedup");
        System.out.println("-----------------,---------------,----------------,----------,-------");
        
        for (int length : TEST_LENGTHS) {
            long totalRecursiveTime = 0;
            long totalIterativeTime = 0;
            int maxStackDepth = 0;
            boolean stackOverflow = false;
            int successfulIterations = 0;
            
            // 多次测试取平均值
            for (int i = 0; i < ITERATIONS; i++) {
                String expression = generateInfixExpression(length);
                
                try {
                    // 测试递归版本
                    long[] recursiveResult = testRecursive(expression);
                    if (recursiveResult == null) {
                        stackOverflow = true;
                        System.out.println("长度 " + length + ": 递归版本发生 StackOverflowError!");
                        break;
                    }
                    totalRecursiveTime += recursiveResult[0];
                    maxStackDepth = Math.max(maxStackDepth, (int) recursiveResult[1]);
                    successfulIterations++;
                    
                    // 测试循环版本
                    totalIterativeTime += testIterative(expression);
                } catch (IOException e) {
                    System.err.println("测试出错: " + e.getMessage());
                } catch (StackOverflowError e) {
                    stackOverflow = true;
                    System.out.println("长度 " + length + ": 递归版本发生 StackOverflowError!");
                    break;
                }
            }
            
            // 计算平均值
            long avgRecursiveTime = successfulIterations > 0 ? totalRecursiveTime / successfulIterations : 0;
            long avgIterativeTime = successfulIterations > 0 ? totalIterativeTime / successfulIterations : 0;
            
            // 创建结果记录
            PerfResult result = new PerfResult(length, avgRecursiveTime, avgIterativeTime, maxStackDepth, stackOverflow);
            results.add(result);
            
            // 控制台输出
            System.out.println(result.toCSVRow());
            
            // 如果栈溢出，停止更长的测试
            if (stackOverflow) {
                System.out.println();
                System.out.println(">>> 递归版本在表达式长度 " + length + " 时发生栈溢出！");
                System.out.println(">>> 循环版本可以继续处理更长的表达式...");
                System.out.println();
                
                // 测试循环版本是否能处理更长的表达式
                for (int longerLength : new int[]{50000, 100000}) {
                    try {
                        String longExpr = generateInfixExpression(longerLength);
                        long iterTime = testIterative(longExpr);
                        PerfResult longerResult = new PerfResult(longerLength, 0, iterTime, 0, true);
                        results.add(longerResult);
                        System.out.println("循环版本成功处理 " + longerLength + " 字符，耗时: " + iterTime + "ms");
                    } catch (IOException e) {
                        System.err.println("IO 错误: " + e.getMessage());
                    }
                }
                break;
            }
        }
        
        System.out.println();
        System.out.println("========================================");
        System.out.println("  测试完成");
        System.out.println("========================================");
        
        return results;
    }
    
    /**
     * 将性能结果保存到 CSV 文件
     * 
     * @param results 性能结果列表
     * @param filePath CSV 文件路径
     * @throws IOException 如果写入文件失败
     */
    public static void saveResultsToCSV(List<PerfResult> results, String filePath) throws IOException {
        // 创建 data 目录（如果不存在）
        File dataDir = new File("data");
        if (!dataDir.exists()) {
            dataDir.mkdirs();
        }
        
        // 写入 CSV 文件
        try (PrintWriter writer = new PrintWriter(new FileWriter(filePath))) {
            // CSV 表头
            writer.println("ExpressionLength,RecursiveTime_ms,IterativeTime_ms,StackDepth,Speedup");
            
            // 数据行
            for (PerfResult result : results) {
                writer.println(result.toCSVRow());
            }
        }
        
        System.out.println();
        System.out.println(">>> 性能数据已保存到: " + filePath);
        System.out.println(">>> 请运行 Python 脚本生成图表: python scripts/plot_perf.py");
    }
    
    /**
     * 程序入口点
     * 
     * @param args 命令行参数
     */
    public static void main(String[] args) {
        System.out.println("编译原理实验 - 尾递归消除性能测试");
        System.out.println();
        
        // 运行性能测试
        List<PerfResult> results = runPerformanceTest();
        
        // 保存结果到 CSV 文件
        try {
            saveResultsToCSV(results, CSV_FILE_PATH);
        } catch (IOException e) {
            System.err.println("保存 CSV 文件失败: " + e.getMessage());
        }
        
        System.out.println();
        System.out.println("提示: 运行 python scripts/plot_perf.py 生成性能对比图表");
    }
}