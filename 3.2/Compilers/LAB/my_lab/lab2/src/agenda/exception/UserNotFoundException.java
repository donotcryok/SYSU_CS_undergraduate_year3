package agenda.exception;

/**
 * 用户未找到异常。
 * 
 * <p>当尝试操作一个不存在的用户时抛出此异常。
 * 该异常由业务逻辑层在用户查询失败时抛出。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class UserNotFoundException extends AgendaException {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 未找到的用户名 */
    private final String username;
    
    /**
     * 构造函数，创建一个带有用户名的异常实例。
     * 
     * @param username 未找到的用户名
     */
    public UserNotFoundException(String username) {
        super("用户不存在: " + username);
        this.username = username;
    }
    
    /**
     * 获取未找到的用户名。
     * 
     * @return 未找到的用户名
     */
    public String getUsername() {
        return username;
    }
}