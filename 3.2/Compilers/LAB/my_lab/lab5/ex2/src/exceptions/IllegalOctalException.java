package exceptions;

/**
 * 八进制字面量包含非法数字 8 或 9 时抛出。
 *
 * <p>Oberon-0 支持 C 风格的八进制字面量 (以 {@code 0} 开头，后跟 {@code 0-7})。
 * 若出现数字 {@code 8} 或 {@code 9}，词法分析器抛出此异常。
 */
public class IllegalOctalException extends RuntimeException {
    private final int line;
    private final int column;

    /**
     * 构造 IllegalOctalException.
     *
     * @param msg    错误描述信息
     * @param line   出错行号
     * @param column 出错列号
     */
    public IllegalOctalException(String msg, int line, int column) {
        super(msg);
        this.line = line;
        this.column = column;
    }

    /** @return 出错行号 */
    public int getLine() { return line; }
    /** @return 出错列号 */
    public int getColumn() { return column; }
}
