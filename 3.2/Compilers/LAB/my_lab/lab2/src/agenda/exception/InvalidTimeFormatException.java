package agenda.exception;

/**
 * 时间格式错误异常。
 * 
 * <p>当用户输入的时间格式不正确时抛出此异常。
 * 该异常由表示层在解析时间字符串失败时抛出。</p>
 * 
 * <p>正确的时间格式应为：yyyy-MM-dd HH:mm:ss</p>
 * 
 * @author 福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class InvalidTimeFormatException extends AgendaException {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 正确的时间格式 */
    public static final String CORRECT_FORMAT = "yyyy-MM-dd HH:mm:ss";
    
    /** 错误的时间输入 */
    private final String invalidInput;
    
    /**
     * 构造函数，创建一个默认的时间格式错误异常实例。
     */
    public InvalidTimeFormatException() {
        super("时间格式错误，正确格式为: " + CORRECT_FORMAT);
        this.invalidInput = null;
    }
    
    /**
     * 构造函数，创建一个带有错误输入的异常实例。
     * 
     * @param input 错误的时间输入
     */
    public InvalidTimeFormatException(String input) {
        super("时间格式错误: \"" + input + "\"，正确格式为: " + CORRECT_FORMAT);
        this.invalidInput = input;
    }
    
    /**
     * 构造函数，创建一个带有详细说明的异常实例。
     * 
     * @param input 错误的时间输入
     * @param detail 额外的错误详情
     */
    public InvalidTimeFormatException(String input, String detail) {
        super("时间格式错误: \"" + input + "\" - " + detail + "，正确格式为: " + CORRECT_FORMAT);
        this.invalidInput = input;
    }
    
    /**
     * 获取错误的时间输入。
     * 
     * @return 错误的时间输入，如果未指定则返回 null
     */
    public String getInvalidInput() {
        return invalidInput;
    }
}