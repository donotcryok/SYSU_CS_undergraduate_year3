package agenda.exception;

/**
 * 用户已存在异常。
 * 
 * <p>当尝试注册一个已存在的用户名时抛出此异常。
 * 该异常由业务逻辑层在用户名唯一性校验失败时抛出。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class UserAlreadyExistsException extends AgendaException {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 已存在的用户名 */
    private final String username;
    
    /**
     * 构造函数，创建一个带有用户名的异常实例。
     * 
     * @param username 已存在的用户名
     */
    public UserAlreadyExistsException(String username) {
        super("用户名已存在: " + username);
        this.username = username;
    }
    
    /**
     * 获取已存在的用户名。
     * 
     * @return 已存在的用户名
     */
    public String getUsername() {
        return username;
    }
}