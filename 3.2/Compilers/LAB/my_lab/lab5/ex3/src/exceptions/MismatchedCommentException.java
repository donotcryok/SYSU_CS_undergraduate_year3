package exceptions;

/**
 * 注释未正确闭合 (缺少 {@code *)} 终结符) 时抛出。
 *
 * <p>Oberon-0 的注释以 {@code (*} 开始、以 {@code *)} 结束。
 * 若到文件末尾仍未找到闭合标记，词法分析器抛出此异常。
 */
public class MismatchedCommentException extends RuntimeException {
    private final int line;
    private final int column;

    /**
     * 构造 MismatchedCommentException.
     *
     * @param msg    错误描述信息
     * @param line   出错行号
     * @param column 出错列号
     */
    public MismatchedCommentException(String msg, int line, int column) {
        super(msg);
        this.line = line;
        this.column = column;
    }

    /** @return 出错行号 */
    public int getLine() { return line; }
    /** @return 出错列号 */
    public int getColumn() { return column; }
}
