package agenda.exception;

/**
 * 密码错误异常。
 * 
 * <p>当用户登录时密码验证失败时抛出此异常。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class InvalidPasswordException extends AgendaException {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * 构造函数，创建一个默认的密码错误异常实例。
     */
    public InvalidPasswordException() {
        super("密码错误");
    }
    
    /**
     * 构造函数，创建一个带有用户名的异常实例。
     * 
     * @param username 密码错误的用户名
     */
    public InvalidPasswordException(String username) {
        super("用户 " + username + " 密码错误");
    }
    
    /**
     * 构造函数，创建一个带有自定义消息的异常实例。
     * 
     * @param message 异常的详细信息
     * @param isCustom 标记是否为自定义消息（保留参数以区分重载）
     */
    public InvalidPasswordException(String message, boolean isCustom) {
        super(message);
    }
}