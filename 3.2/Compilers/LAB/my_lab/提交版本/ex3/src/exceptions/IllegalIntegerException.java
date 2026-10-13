package exceptions;

/**
 * 数字与标识符粘连 (如 {@code 123abc}) 时抛出。
 *
 * <p>Oberon-0 的数字字面量必须为纯数字序列，若数字后紧跟字母或数字，
 * 词法分析器抛出此异常。
 */
public class IllegalIntegerException extends RuntimeException {
    private final int line;
    private final int column;

    /**
     * 构造 IllegalIntegerException.
     *
     * @param msg    错误描述信息
     * @param line   出错行号
     * @param column 出错列号
     */
    public IllegalIntegerException(String msg, int line, int column) {
        super(msg);
        this.line = line;
        this.column = column;
    }

    /** @return 出错行号 */
    public int getLine() { return line; }
    /** @return 出错列号 */
    public int getColumn() { return column; }
}
