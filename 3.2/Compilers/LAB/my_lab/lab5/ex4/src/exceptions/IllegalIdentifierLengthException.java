package exceptions;

/**
 * 标识符长度超出 24 字符限制时抛出。
 *
 * <p>Oberon-0 语言规定标识符 (ident) 最大长度为 24 个字符。
 * 当词法分析器检测到超长标识符时抛出此异常。
 */
public class IllegalIdentifierLengthException extends RuntimeException {
    private final int line;
    private final int column;

    /**
     * 构造 IllegalIdentifierLengthException.
     *
     * @param msg    错误描述信息
     * @param line   出错行号
     * @param column 出错列号
     */
    public IllegalIdentifierLengthException(String msg, int line, int column) {
        super(msg);
        this.line = line;
        this.column = column;
    }

    /** @return 出错行号 */
    public int getLine() { return line; }
    /** @return 出错列号 */
    public int getColumn() { return column; }
}
