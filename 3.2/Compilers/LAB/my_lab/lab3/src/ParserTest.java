import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.util.List;

/**
 * Parser 类的 JUnit 单元测试
 * 
 * <p>测试覆盖以下场景：
 * <ul>
 *   <li>正常中缀表达式转换</li>
 *   <li>词法错误检测（非法字符、空白符）</li>
 *   <li>语法错误检测（缺少运算量、连续运算符）</li>
 *   <li>错误恢复机制（Panic-Mode）</li>
 *   <li>边界情况（空输入、单数字等）</li>
 * </ul>
 * 
 * @author 编译原理实验
 * @version 2.0
 * @since 2024
 */
public class ParserTest {
    
    /** 用于捕获标准输出的流 */
    private ByteArrayOutputStream outContent;
    
    /** 用于捕获标准错误输出的流 */
    private ByteArrayOutputStream errContent;
    
    /** 原始标准输出流 */
    private PrintStream originalOut;
    
    /** 原始标准错误流 */
    private PrintStream originalErr;
    
    /**
     * 测试前初始化：重定向标准输出和错误流
     */
    @Before
    public void setUpStreams() {
        outContent = new ByteArrayOutputStream();
        errContent = new ByteArrayOutputStream();
        originalOut = System.out;
        originalErr = System.err;
        System.setOut(new PrintStream(outContent));
        System.setErr(new PrintStream(errContent));
    }
    
    /**
     * 测试后恢复：还原标准输出和错误流
     */
    @After
    public void restoreStreams() {
        System.setOut(originalOut);
        System.setErr(originalErr);
    }
    
    // ==================== 正常表达式测试 ====================
    
    /**
     * 测试单个数字
     * 输入: "5"
     * 期望输出: "5"
     */
    @Test
    public void testSingleDigit() throws IOException {
        Parser parser = createParser("5\n");
        parser.expr();
        assertEquals("5", outContent.toString().trim());
        assertFalse(parser.hasErrors());
    }
    
    /**
     * 测试简单加法
     * 输入: "1+2"
     * 期望输出: "12+"
     */
    @Test
    public void testSimpleAddition() throws IOException {
        Parser parser = createParser("1+2\n");
        parser.expr();
        assertEquals("12+", outContent.toString().trim());
        assertFalse(parser.hasErrors());
    }
    
    /**
     * 测试简单减法
     * 输入: "9-3"
     * 期望输出: "93-"
     */
    @Test
    public void testSimpleSubtraction() throws IOException {
        Parser parser = createParser("9-3\n");
        parser.expr();
        assertEquals("93-", outContent.toString().trim());
        assertFalse(parser.hasErrors());
    }
    
    /**
     * 测试多个运算符
     * 输入: "1+2-3+4"
     * 期望输出: "12+3-4+"
     */
    @Test
    public void testMultipleOperators() throws IOException {
        Parser parser = createParser("1+2-3+4\n");
        parser.expr();
        assertEquals("12+3-4+", outContent.toString().trim());
        assertFalse(parser.hasErrors());
    }
    
    /**
     * 测试长表达式
     * 输入: "1+2+3+4+5+6+7+8+9"
     * 期望输出: "12+3+4+5+6+7+8+9+"
     */
    @Test
    public void testLongExpression() throws IOException {
        Parser parser = createParser("1+2+3+4+5+6+7+8+9\n");
        parser.expr();
        assertEquals("12+3+4+5+6+7+8+9+", outContent.toString().trim());
        assertFalse(parser.hasErrors());
    }
    
    // ==================== 词法错误测试 ====================
    
    /**
     * 测试空格字符（词法错误）
     * 输入: "1 + 2"
     * 期望: 报告词法错误，空格打断表达式连续性
     */
    @Test
    public void testWhitespaceError() throws IOException {
        Parser parser = createParser("1 + 2\n");
        parser.expr();
        // 空格打断表达式，只输出第一个数字
        assertEquals("1", outContent.toString().trim());
        assertTrue(parser.hasErrors());
        // 检查错误类型
        List<Parser.CompileError> errors = parser.getErrors();
        // 应该有空格错误和多余字符错误
        assertTrue(errors.size() >= 1);
        // 第一个错误应该是词法错误（空格）
        assertEquals(Parser.CompileError.ErrorType.LEXICAL_ERROR, errors.get(0).type);
    }
    
    /**
     * 测试制表符（词法错误）
     * 输入: "1\t+2"
     * 期望: 报告词法错误
     */
    @Test
    public void testTabError() throws IOException {
        Parser parser = createParser("1\t+2\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        assertEquals(Parser.CompileError.ErrorType.LEXICAL_ERROR, errors.get(0).type);
        assertTrue(errors.get(0).message.contains("空白符"));
    }
    
    /**
     * 测试非法字符（词法错误）
     * 输入: "1a+2"
     * 期望: 报告词法错误，恢复后继续解析
     */
    @Test
    public void testInvalidCharacter() throws IOException {
        Parser parser = createParser("1a+2\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        assertEquals(Parser.CompileError.ErrorType.LEXICAL_ERROR, errors.get(0).type);
        assertTrue(errors.get(0).message.contains("非法字符"));
    }
    
    /**
     * 测试多个非法字符
     * 输入: "1@#2"
     * 期望: 报告多个错误（词法错误和可能的语法错误）
     */
    @Test
    public void testMultipleInvalidCharacters() throws IOException {
        Parser parser = createParser("1@#2\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        // 应该有多个错误
        assertTrue(errors.size() >= 2);
        // 第一个错误应该是词法错误（@）
        assertEquals(Parser.CompileError.ErrorType.LEXICAL_ERROR, errors.get(0).type);
    }
    
    // ==================== 语法错误测试 ====================
    
    /**
     * 测试缺少左运算量
     * 输入: "+1"
     * 期望: 报告语法错误
     */
    @Test
    public void testMissingLeftOperand() throws IOException {
        Parser parser = createParser("+1\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        assertEquals(Parser.CompileError.ErrorType.SYNTAX_ERROR, errors.get(0).type);
    }
    
    /**
     * 测试缺少右运算量
     * 输入: "1+"
     * 期望: 报告语法错误
     */
    @Test
    public void testMissingRightOperand() throws IOException {
        Parser parser = createParser("1+\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        boolean hasMissingOperandError = errors.stream()
            .anyMatch(e -> e.message.contains("缺少右运算量"));
        assertTrue(hasMissingOperandError);
    }
    
    /**
     * 测试连续运算符
     * 输入: "1++2"
     * 期望: 报告语法错误
     */
    @Test
    public void testConsecutiveOperators() throws IOException {
        Parser parser = createParser("1++2\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        boolean hasConsecutiveError = errors.stream()
            .anyMatch(e -> e.message.contains("连续的运算符"));
        assertTrue(hasConsecutiveError);
    }
    
    /**
     * 测试多个连续运算符
     * 输入: "1+-2"
     * 期望: 报告语法错误
     */
    @Test
    public void testMixedConsecutiveOperators() throws IOException {
        Parser parser = createParser("1+-2\n");
        parser.expr();
        assertTrue(parser.hasErrors());
    }
    
    /**
     * 测试表达式结束后多余字符
     * 输入: "1+2x"
     * 期望: 报告错误
     */
    @Test
    public void testExtraCharactersAfterExpression() throws IOException {
        Parser parser = createParser("1+2x\n");
        parser.expr();
        assertTrue(parser.hasErrors());
    }
    
    // ==================== 边界情况测试 ====================
    
    /**
     * 测试空输入
     * 期望: 报告语法错误
     */
    @Test
    public void testEmptyInput() throws IOException {
        Parser parser = createParser("\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        boolean hasEmptyError = errors.stream()
            .anyMatch(e -> e.message.contains("表达式为空"));
        assertTrue(hasEmptyError);
    }
    
    /**
     * 测试只有运算符
     * 输入: "+"
     * 期望: 报告语法错误
     */
    @Test
    public void testOnlyOperator() throws IOException {
        Parser parser = createParser("+\n");
        parser.expr();
        assertTrue(parser.hasErrors());
    }
    
    /**
     * 测试只有非法字符
     * 输入: "@#$"
     * 期望: 报告多个词法错误
     */
    @Test
    public void testOnlyInvalidCharacters() throws IOException {
        Parser parser = createParser("@#$\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        assertTrue(errors.size() >= 3);
    }
    
    // ==================== 错误定位测试 ====================
    
    /**
     * 测试错误位置定位
     * 输入: "1+ 2"
     * 期望: 错误位置应该是第3个字符（空格）
     */
    @Test
    public void testErrorPosition() throws IOException {
        Parser parser = createParser("1+ 2\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        // 空格在位置3（1-based）
        assertEquals(3, errors.get(0).position);
    }
    
    /**
     * 测试多个错误的独立定位
     * 输入: "1 + 2 + 3"
     * 期望: 空格打断表达式，报告错误
     */
    @Test
    public void testMultipleErrorPositions() throws IOException {
        Parser parser = createParser("1 + 2 + 3\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        // 应该有多个错误（空格打断表达式）
        assertTrue(errors.size() >= 1);
        // 第一个错误应该是词法错误（空格），位置在2
        assertEquals(Parser.CompileError.ErrorType.LEXICAL_ERROR, errors.get(0).type);
        assertEquals(2, errors.get(0).position); // 第一个空格
    }
    
    // ==================== 错误恢复测试 ====================
    
    /**
     * 测试 Panic-Mode 恢复
     * 输入: "1@+2"
     * 期望: 报告@的错误，@打断表达式，只输出第一个数字
     */
    @Test
    public void testPanicModeRecovery() throws IOException {
        Parser parser = createParser("1@+2\n");
        parser.expr();
        // @打断表达式，只输出第一个数字
        assertEquals("1", outContent.toString().trim());
        assertTrue(parser.hasErrors());
        // 第一个错误应该是词法错误（@）
        List<Parser.CompileError> errors = parser.getErrors();
        assertEquals(Parser.CompileError.ErrorType.LEXICAL_ERROR, errors.get(0).type);
    }
    
    /**
     * 测试多个错误恢复
     * 输入: "1@2#3"
     * 期望: 报告两个错误，但能继续解析
     */
    @Test
    public void testMultipleErrorRecovery() throws IOException {
        Parser parser = createParser("1@2#3\n");
        parser.expr();
        assertTrue(parser.hasErrors());
        List<Parser.CompileError> errors = parser.getErrors();
        assertTrue(errors.size() >= 2);
    }
    
    // ==================== 辅助方法 ====================
    
    /**
     * 创建解析器实例
     * 
     * @param input 输入字符串
     * @return 配置好的 Parser 实例
     * @throws IOException 如果创建失败
     */
    private Parser createParser(String input) throws IOException {
        return new Parser(new ByteArrayInputStream(input.getBytes()));
    }
}