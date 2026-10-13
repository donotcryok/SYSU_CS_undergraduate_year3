
/**
 * Oberon-0 词法单元 (自包含, 无 CUP 依赖).
 * 每个 Token 记录类型码、行列号及可选的语义值.
 */
public class Token {

    // ---- Token 类型常量 ----
    public static final int EOF            =  0;
    public static final int ERROR          = -1;

    // 保留字
    public static final int MODULE         =  1;
    public static final int BEGIN          =  2;
    public static final int END            =  3;
    public static final int IF             =  4;
    public static final int THEN           =  5;
    public static final int ELSIF          =  6;
    public static final int ELSE           =  7;
    public static final int WHILE          =  8;
    public static final int DO             =  9;
    public static final int PROCEDURE      = 10;
    public static final int VAR            = 11;
    public static final int CONST          = 12;
    public static final int TYPE           = 13;
    public static final int RECORD         = 14;
    public static final int ARRAY          = 15;
    public static final int OF             = 16;

    // 预定义关键字
    public static final int INTEGER_TYPE   = 17;
    public static final int BOOLEAN_TYPE   = 18;
    public static final int READ           = 19;
    public static final int WRITE          = 20;
    public static final int WRITELN        = 21;

    // 字面量
    public static final int INTEGER        = 22;
    public static final int BOOL_LIT       = 23;

    // 标识符
    public static final int IDENT          = 24;

    // 运算符
    public static final int PLUS           = 30;
    public static final int MINUS          = 31;
    public static final int STAR           = 32;
    public static final int DIV            = 33;
    public static final int MOD            = 34;
    public static final int AND            = 35;
    public static final int OR             = 36;
    public static final int NOT            = 37;
    public static final int EQ             = 38;
    public static final int NEQ            = 39;
    public static final int LT             = 40;
    public static final int LE             = 41;
    public static final int GT             = 42;
    public static final int GE             = 43;

    // 分界符
    public static final int ASSIGN         = 50;
    public static final int COLON          = 51;
    public static final int SEMI           = 52;
    public static final int DOT            = 53;
    public static final int COMMA          = 54;
    public static final int LPAREN         = 55;
    public static final int RPAREN         = 56;
    public static final int LBRACK         = 57;
    public static final int RBRACK         = 58;

    // ---- 实例字段 ----
    /** Token 类型码 (见本类常量定义) */
    public final int type;
    /** Token 所在行号 (从 1 开始) */
    public final int line;
    /** Token 所在列号 (从 0 开始) */
    public final int column;
    /** 可选的语义值 (标识符名字符串 / 整数值 / 布尔值)，无值时可为 {@code null} */
    public final Object value;

    /**
     * 创建 Token (无语义值).
     *
     * @param type   Token 类型码
     * @param line   行号
     * @param column 列号
     */
    public Token(int type, int line, int column) {
        this(type, line, column, null);
    }

    /**
     * 创建 Token (带语义值).
     *
     * @param type   Token 类型码
     * @param line   行号
     * @param column 列号
     * @param value  语义值 (如标识符名、整数、布尔值)
     */
    public Token(int type, int line, int column, Object value) {
        this.type   = type;
        this.line   = line;
        this.column = column;
        this.value  = value;
    }

    /**
     * 将 Token 类型码转为可读字符串.
     *
     * @param type Token 类型码
     * @return 类型对应的可读名称 (如 "MODULE", ";", "IDENT")
     */
    public static String typeName(int type) {
        switch (type) {
            case EOF:           return "EOF";
            case MODULE:        return "MODULE";
            case BEGIN:         return "BEGIN";
            case END:           return "END";
            case IF:            return "IF";
            case THEN:          return "THEN";
            case ELSIF:         return "ELSIF";
            case ELSE:          return "ELSE";
            case WHILE:         return "WHILE";
            case DO:            return "DO";
            case PROCEDURE:     return "PROCEDURE";
            case VAR:           return "VAR";
            case CONST:         return "CONST";
            case TYPE:          return "TYPE";
            case RECORD:        return "RECORD";
            case ARRAY:         return "ARRAY";
            case OF:            return "OF";
            case INTEGER_TYPE:  return "INTEGER_TYPE";
            case BOOLEAN_TYPE:  return "BOOLEAN_TYPE";
            case READ:          return "READ";
            case WRITE:         return "WRITE";
            case WRITELN:       return "WRITELN";
            case INTEGER:       return "INTEGER";
            case BOOL_LIT:      return "BOOL_LIT";
            case IDENT:         return "IDENT";
            case PLUS:          return "+";
            case MINUS:         return "-";
            case STAR:          return "*";
            case DIV:           return "DIV";
            case MOD:           return "MOD";
            case AND:           return "&";
            case OR:            return "OR";
            case NOT:           return "~";
            case EQ:            return "=";
            case NEQ:           return "#";
            case LT:            return "<";
            case LE:            return "<=";
            case GT:            return ">";
            case GE:            return ">=";
            case ASSIGN:        return ":=";
            case COLON:         return ":";
            case SEMI:          return ";";
            case DOT:           return ".";
            case COMMA:         return ",";
            case LPAREN:        return "(";
            case RPAREN:        return ")";
            case LBRACK:        return "[";
            case RBRACK:        return "]";
            default:            return "UNKNOWN";
        }
    }

    /**
     * 返回 Token 的调试用字符串表示: {@code (行,列) 类型名 [语义值]}.
     *
     * @return 格式化字符串
     */
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("(%d,%d) ", line, column));
        sb.append(typeName(type));
        if (value != null) {
            sb.append(" [").append(value).append("]");
        }
        return sb.toString();
    }
}
