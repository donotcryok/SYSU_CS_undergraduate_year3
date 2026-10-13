import java.io.*;
import java_cup.runtime.*;
import java.util.HashMap;
import java.util.Map;

/**
 * CupScanner —— 将 OberonScanner (Token) 桥接到 JavaCUP Scanner (Symbol) 接口.
 *
 * <p>JavaCUP 要求词法分析器实现 {@link java_cup.runtime.Scanner}，返回
 * {@link java_cup.runtime.Symbol} 对象。Token 的类型码与 {@code sym} 的类型码不同
 * (JavaCUP 按声明顺序重新编号)，因此需要通过映射表进行转换。
 */
public class CupScanner implements java_cup.runtime.Scanner {

    /** 内部持有的 Oberon-0 词法扫描器 */
    private OberonScanner scanner;

    /** Token 类型码 → sym 符号常量的映射 (共 49 对) */
    private static final Map<Integer, Integer> TOKEN_MAP = new HashMap<>();

    static {
        TOKEN_MAP.put(Token.EOF,           sym.EOF);
        TOKEN_MAP.put(Token.MODULE,        sym.MODULE);
        TOKEN_MAP.put(Token.BEGIN,         sym.BEGIN);
        TOKEN_MAP.put(Token.END,           sym.END);
        TOKEN_MAP.put(Token.IF,            sym.IF);
        TOKEN_MAP.put(Token.THEN,          sym.THEN);
        TOKEN_MAP.put(Token.ELSIF,         sym.ELSIF);
        TOKEN_MAP.put(Token.ELSE,          sym.ELSE);
        TOKEN_MAP.put(Token.WHILE,         sym.WHILE);
        TOKEN_MAP.put(Token.DO,            sym.DO);
        TOKEN_MAP.put(Token.PROCEDURE,     sym.PROCEDURE);
        TOKEN_MAP.put(Token.VAR,           sym.VAR);
        TOKEN_MAP.put(Token.CONST,         sym.CONST);
        TOKEN_MAP.put(Token.TYPE,          sym.TYPE);
        TOKEN_MAP.put(Token.RECORD,        sym.RECORD);
        TOKEN_MAP.put(Token.ARRAY,         sym.ARRAY);
        TOKEN_MAP.put(Token.OF,            sym.OF);
        TOKEN_MAP.put(Token.INTEGER_TYPE,  sym.INTEGER_TYPE);
        TOKEN_MAP.put(Token.BOOLEAN_TYPE,  sym.BOOLEAN_TYPE);
        TOKEN_MAP.put(Token.READ,          sym.READ);
        TOKEN_MAP.put(Token.WRITE,         sym.WRITE);
        TOKEN_MAP.put(Token.WRITELN,       sym.WRITELN);
        TOKEN_MAP.put(Token.INTEGER,       sym.INTEGER);
        TOKEN_MAP.put(Token.BOOL_LIT,      sym.BOOL_LIT);
        TOKEN_MAP.put(Token.IDENT,         sym.IDENT);
        TOKEN_MAP.put(Token.PLUS,          sym.PLUS);
        TOKEN_MAP.put(Token.MINUS,         sym.MINUS);
        TOKEN_MAP.put(Token.STAR,          sym.STAR);
        TOKEN_MAP.put(Token.DIV,           sym.DIV);
        TOKEN_MAP.put(Token.MOD,           sym.MOD);
        TOKEN_MAP.put(Token.AND,           sym.AND);
        TOKEN_MAP.put(Token.OR,            sym.OR);
        TOKEN_MAP.put(Token.NOT,           sym.NOT);
        TOKEN_MAP.put(Token.EQ,            sym.EQ);
        TOKEN_MAP.put(Token.NEQ,           sym.NEQ);
        TOKEN_MAP.put(Token.LT,            sym.LT);
        TOKEN_MAP.put(Token.LE,            sym.LE);
        TOKEN_MAP.put(Token.GT,            sym.GT);
        TOKEN_MAP.put(Token.GE,            sym.GE);
        TOKEN_MAP.put(Token.ASSIGN,        sym.ASSIGN);
        TOKEN_MAP.put(Token.COLON,         sym.COLON);
        TOKEN_MAP.put(Token.SEMI,          sym.SEMI);
        TOKEN_MAP.put(Token.DOT,           sym.DOT);
        TOKEN_MAP.put(Token.COMMA,         sym.COMMA);
        TOKEN_MAP.put(Token.LPAREN,        sym.LPAREN);
        TOKEN_MAP.put(Token.RPAREN,        sym.RPAREN);
        TOKEN_MAP.put(Token.LBRACK,        sym.LBRACK);
        TOKEN_MAP.put(Token.RBRACK,        sym.RBRACK);
    }

    /**
     * 构造 CupScanner.
     *
     * @param in 输入流 Reader (通常为 new FileReader(源文件路径))
     */
    public CupScanner(Reader in) {
        this.scanner = new OberonScanner(in);
    }

    /**
     * 读取下一个 Symbol.
     *
     * <p>内部调用 OberonScanner.yylex() 获取 Token，通过映射表转换为 Symbol。
     *
     * @return JavaCUP 所需的 Symbol 对象
     * @throws Exception 词法分析过程中的异常 (如非法字符等)
     */
    @Override
    public Symbol next_token() throws Exception {
        Token t = scanner.yylex();
        if (t == null) {
            return new Symbol(sym.EOF);
        }
        Integer symType = TOKEN_MAP.get(t.type);
        if (symType == null) {
            throw new RuntimeException(
                "未知 Token 类型: " + t.type + " (" + Token.typeName(t.type) + ")");
        }
        return new Symbol(symType, t.line, t.column, t.value);
    }
}
