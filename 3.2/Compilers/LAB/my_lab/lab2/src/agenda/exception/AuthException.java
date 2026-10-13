package agenda.exception;

/**
 * 认证异常（密码错误异常）。
 * 
 * <p>当用户登录时密码验证失败时抛出此异常。
 * 该异常由业务逻辑层在密码校验失败时抛出。</p>
 * 
 * @author 福泉
 * @version 1.0
 * @since 2026-03
 */
public class AuthException extends AgendaException {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 认证失败的用户名 */
    private final String username;
    
    /**
     * 构造函数，创建一个默认的认证异常实例。
     */
    public AuthException() {
        super("密码错误");
        this.username = null;
    }
    
    /**
     * 构造函数，创建一个带有用户名的异常实例。
     * 
     * @param username 认证失败的用户名
     */
    public AuthException(String username) {
        super("用户 " + username + " 密码错误");
        this.username = username;
    }
    
    /**
     * 获取认证失败的用户名。
     * 
     * @return 认证失败的用户名，如果未指定则返回 null
     */
    public String getUsername() {
        return username;
    }
}