package exceptions;

/**
 * 遇到非法字符 (不在 Oberon-0 字符集中) 时抛出。
 *
 * <p>Oberon-0 语言仅接受 ASCII 可打印字符集的一个子集。
 * 若输入中出现无法识别的字符 (如 {@code @}、{@code $} 等)，词法分析器抛出此异常。
 */
public class IllegalSymbolException extends RuntimeException {
    private final int line;
    private final int column;

    /**
     * 构造 IllegalSymbolException.
     *
     * @param msg    错误描述信息
     * @param line   出错行号
     * @param column 出错列号
     */
    public IllegalSymbolException(String msg, int line, int column) {
        super(msg);
        this.line = line;
        this.column = column;
    }

    /** @return 出错行号 */
    public int getLine() { return line; }
    /** @return 出错列号 */
    public int getColumn() { return column; }
}
