package agenda.exception;

/**
 * Agenda 系统基础异常类。
 * 
 * <p>所有 Agenda 系统的自定义异常都继承自此类。
 * 该类提供了统一的异常处理基类，便于异常的分类和处理。</p>
 * 
 * <p>异常处理机制设计原则：
 * - 业务逻辑层遇到任何校验失败时，抛出对应的自定义异常
 * - 表示层捕获异常并格式化输出友好错误信息
 * - 完美分离正常逻辑与异常处理代码</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03
 */
public class AgendaException extends Exception {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /**
     * 构造函数，创建一个不带详细信息的异常实例。
     */
    public AgendaException() {
        super();
    }
    
    /**
     * 构造函数，创建一个带有详细信息的异常实例。
     * 
     * @param message 异常的详细信息
     */
    public AgendaException(String message) {
        super(message);
    }
    
    /**
     * 构造函数，创建一个带有详细信息和原因的异常实例。
     * 
     * @param message 异常的详细信息
     * @param cause 导致此异常的原因
     */
    public AgendaException(String message, Throwable cause) {
        super(message, cause);
    }
    
    /**
     * 构造函数，创建一个带有原因的异常实例。
     * 
     * @param cause 导致此异常的原因
     */
    public AgendaException(Throwable cause) {
        super(cause);
    }
}