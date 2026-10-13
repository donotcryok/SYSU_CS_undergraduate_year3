import java.io.*;
import java.util.ArrayList;
import java.util.List;

/**
 * 后缀表达式转换器 - 编译原理实验
 *
 * <p>本程序实现中缀表达式到后缀表达式的转换，包含以下功能：
 * <ul>
 *   <li>静态与非静态成员重构（支持多实例隔离）</li>
 *   <li>尾递归消除（使用 while 循环替代）</li>
 *   <li>高级错误处理与恢复（词法错误/语法错误分类、错误定位、Panic-Mode 恢复）</li>
 * </ul>
 *
 * @author 编译原理实验
 * @version 2.0
 * @since 2024
 */
class Parser {
    /** 当前向前看字符，改为非静态以支持多实例隔离 */
    private int lookahead;
    
    /** 当前字符位置索引，用于错误定位 */
    private int position;
    
    /** 输入流读取器 */
    private PushbackReader reader;
    
    /** 错误收集列表，支持一次运行报出多个错误 */
    private List<CompileError> errors;
    
    /** 同步记号集合：用于 Panic-Mode 恢复的合法继续字符 */
    private static final String SYNC_TOKENS = "0123456789+-";
    
    /**
     * 编译错误内部类
     *
     * <p>封装错误类型、位置和详细信息，支持词法错误和语法错误的分类。
     */
    static class CompileError {
        /** 错误类型枚举 */
        enum ErrorType {
            /** 词法错误：非法字符、空白符等 */
            LEXICAL_ERROR("词法错误"),
            /** 语法错误：缺少运算量、运算符连续等 */
            SYNTAX_ERROR("语法错误");
            
            private final String description;
            
            ErrorType(String description) {
                this.description = description;
            }
            
            @Override
            public String toString() {
                return description;
            }
        }
        
        /** 错误类型 */
        final ErrorType type;
        /** 错误位置索引 */
        final int position;
        /** 错误字符 */
        final char character;
        /** 错误详细信息 */
        final String message;
        
        /**
         * 构造编译错误对象
         *
         * @param type 错误类型
         * @param position 错误位置索引
         * @param character 引起错误的字符
         * @param message 错误详细信息
         */
        CompileError(ErrorType type, int position, char character, String message) {
            this.type = type;
            this.position = position;
            this.character = character;
            this.message = message;
        }
        
        @Override
        public String toString() {
            return String.format("[%s] 位置 %d: 字符 '%s' - %s",
                    type, position,
                    character == '\t' ? "\\t" :
                    character == ' ' ? "空格" :
                    character == '\n' ? "\\n" :
                    character == '\r' ? "\\r" :
                    character == -1 ? "EOF" : character,
                    message);
        }
    }
    
    /**
     * 构造解析器，初始化输入流和状态
     *
     * @param inputStream 输入流
     * @throws IOException 如果读取输入流时发生 I/O 错误
     */
    public Parser(InputStream inputStream) throws IOException {
        this.reader = new PushbackReader(new InputStreamReader(inputStream), 2);
        this.lookahead = -1;
        this.position = 0;
        this.errors = new ArrayList<>();
        advance(); // 读取第一个字符
    }
    
    /**
     * 向前移动一个字符，更新 lookahead 和 position
     *
     * @throws IOException 如果读取输入流时发生 I/O 错误
     */
    private void advance() throws IOException {
        lookahead = reader.read();
        if (lookahead != -1) {
            position++;
        }
    }
    
    /**
     * 检查当前字符是否为空白符（不包括换行符）
     *
     * <p>换行符被视为表达式结束符，不作为空白符处理。
     *
     * @return 如果是空白符返回 true
     */
    private boolean isWhitespace() {
        return lookahead == ' ' || lookahead == '\t';
    }
    
    /**
     * 检查当前字符是否为表达式结束符
     *
     * <p>换行符和 EOF 都被视为表达式结束符。
     *
     * @return 如果是结束符返回 true
     */
    private boolean isEndMarker() {
        return lookahead == '\n' || lookahead == '\r' || lookahead == -1;
    }
    
    /**
     * 检查当前字符是否为合法的词法单元
     *
     * @return 如果是合法字符（数字或运算符）返回 true
     */
    private boolean isValidToken() {
        return Character.isDigit((char) lookahead) ||
               lookahead == '+' || lookahead == '-';
    }
    
    /**
     * 跳过非法字符并报告词法错误
     *
     * <p>实现 Panic-Mode 恢复机制：遇到非法字符时，
     * 跳过直到遇到下一个合法的操作数或运算符，或遇到表达式结束符。
     *
     * @throws IOException 如果读取输入流时发生 I/O 错误
     */
    private void skipInvalidTokens() throws IOException {
        while (!isEndMarker() && !isValidToken()) {
            if (isWhitespace()) {
                // 空白符作为词法错误报告
                errors.add(new CompileError(
                    CompileError.ErrorType.LEXICAL_ERROR,
                    position,
                    (char) lookahead,
                    "表达式中不允许包含空白符"
                ));
            } else {
                // 其他非法字符作为词法错误报告
                errors.add(new CompileError(
                    CompileError.ErrorType.LEXICAL_ERROR,
                    position,
                    (char) lookahead,
                    "非法字符: 不是有效的数字或运算符"
                ));
            }
            advance();
        }
    }
    
    /**
     * 解析并输出后缀表达式
     *
     * <p>这是语法分析的入口方法，解析整个表达式。
     *
     * @throws IOException 如果读取输入流时发生 I/O 错误
     */
    void expr() throws IOException {
        // 跳过开头的非法字符
        skipInvalidTokens();
        
        if (isEndMarker()) {
            errors.add(new CompileError(
                CompileError.ErrorType.SYNTAX_ERROR,
                position,
                (char) -1,
                "表达式为空"
            ));
            return;
        }
        
        term();
        rest();
        
        // 检查是否还有未处理的字符（跳过空白符后）
        skipInvalidTokens();
        if (!isEndMarker()) {
            errors.add(new CompileError(
                CompileError.ErrorType.SYNTAX_ERROR,
                position,
                (char) lookahead,
                "表达式结束后存在多余字符"
            ));
        }
    }
    
    /**
     * 解析剩余部分（消除尾递归版本）
     *
     * <p>原始版本使用尾递归实现：
     * <pre>
     * void rest() {
     *     if (lookahead == '+') {
     *         match('+'); term(); System.out.write('+'); rest();
     *     } else if (lookahead == '-') {
     *         match('-'); term(); System.out.write('-'); rest();
     *     }
     * }
     * </pre>
     *
     * <p>重构为 while 循环版本，避免栈溢出，提高执行效率：
     * <ul>
     *   <li>消除递归调用开销</li>
     *   <li>支持超长表达式解析（无栈深度限制）</li>
     *   <li>便于性能对比测试</li>
     * </ul>
     *
     * @throws IOException 如果读取输入流时发生 I/O 错误
     */
    void rest() throws IOException {
        while (lookahead == '+' || lookahead == '-') {
            int op = lookahead;
            
            // 尝试匹配运算符
            if (!match(op)) {
                // 匹配失败，Panic-Mode 恢复
                skipInvalidTokens();
                continue;
            }
            
            // 跳过运算符后可能的非法字符
            skipInvalidTokens();
            
            // 检查是否有右运算量
            if (isEndMarker()) {
                errors.add(new CompileError(
                    CompileError.ErrorType.SYNTAX_ERROR,
                    position,
                    (char) op,
                    "运算符 '" + (char) op + "' 缺少右运算量"
                ));
                break;
            }
            
            // 检查是否连续运算符
            if (lookahead == '+' || lookahead == '-') {
                errors.add(new CompileError(
                    CompileError.ErrorType.SYNTAX_ERROR,
                    position,
                    (char) lookahead,
                    "连续的运算符，缺少运算量"
                ));
                // Panic-Mode: 跳过当前运算符，继续尝试解析
                advance();
                skipInvalidTokens();
                continue;
            }
            
            term();
            System.out.write(op);
        }
    }
    
    /**
     * 解析项（数字）
     *
     * <p>项是表达式的最基本单元，必须是数字字符。
     * 如果遇到非数字字符，报告语法错误并尝试恢复。
     *
     * @throws IOException 如果读取输入流时发生 I/O 错误
     */
    void term() throws IOException {
        if (Character.isDigit((char) lookahead)) {
            System.out.write((char) lookahead);
            match(lookahead);
        } else {
            // 语法错误：期望数字但遇到其他字符
            errors.add(new CompileError(
                CompileError.ErrorType.SYNTAX_ERROR,
                position,
                (char) lookahead,
                "期望数字，但遇到 '" + (char) lookahead + "'"
            ));
            // Panic-Mode 恢复：跳过当前字符
            advance();
        }
    }
    
    /**
     * 匹配并消费指定字符
     *
     * <p>如果当前向前看字符与期望字符匹配，则消费它并读取下一个字符；
     * 否则报告语法错误。
     *
     * @param t 期望匹配的字符
     * @return 如果匹配成功返回 true，否则返回 false
     * @throws IOException 如果读取输入流时发生 I/O 错误
     */
    boolean match(int t) throws IOException {
        if (lookahead == t) {
            advance();
            return true;
        } else {
            errors.add(new CompileError(
                CompileError.ErrorType.SYNTAX_ERROR,
                position,
                (char) lookahead,
                "期望 '" + (char) t + "'，但遇到 '" + (char) lookahead + "'"
            ));
            return false;
        }
    }
    
    /**
     * 获取收集到的所有错误
     *
     * @return 错误列表
     */
    List<CompileError> getErrors() {
        return errors;
    }
    
    /**
     * 检查是否存在错误
     *
     * @return 如果存在错误返回 true
     */
    boolean hasErrors() {
        return !errors.isEmpty();
    }
    
    /**
     * 打印所有收集到的错误信息
     */
    void printErrors() {
        if (errors.isEmpty()) {
            System.err.println("没有发现错误。");
            return;
        }
        System.err.println("\n========== 编译错误报告 ==========");
        System.err.println("共发现 " + errors.size() + " 个错误:\n");
        for (int i = 0; i < errors.size(); i++) {
            System.err.println("错误 " + (i + 1) + ": " + errors.get(i));
        }
        System.err.println("\n=================================");
    }
}

/**
 * 后缀表达式转换主程序
 *
 * <p>本程序演示编译原理中的语法分析技术，将中缀表达式转换为后缀表达式（逆波兰表示）。
 *
 * <h2>功能特性</h2>
 * <ul>
 *   <li>支持单个数字（0-9）和加减运算符（+、-）</li>
 *   <li>词法错误检测：非法字符、空白符</li>
 *   <li>语法错误检测：缺少运算量、连续运算符</li>
 *   <li>错误恢复：Panic-Mode 机制，一次运行报告多个错误</li>
 *   <li>错误定位：精确报告错误位置和字符</li>
 * </ul>
 *
 * <h2>使用方法</h2>
 * <pre>
 * java Postfix
 * Input an infix expression: 1+2-3
 * Output postfix notation: 12+3-
 * </pre>
 *
 * @author 编译原理实验
 * @version 2.0
 * @since 2024
 */
public class Postfix {
    /**
     * 程序入口点
     *
     * @param args 命令行参数（未使用）
     * @throws IOException 如果读取输入时发生 I/O 错误
     */
    public static void main(String[] args) throws IOException {
        System.out.println("Input an infix expression and output its postfix notation:");
        System.out.print(">>> ");
        
        Parser parser = new Parser(System.in);
        parser.expr();
        
        System.out.println();
        
        if (parser.hasErrors()) {
            parser.printErrors();
        }
        
        System.out.println("\nEnd of program.");
    }
}
