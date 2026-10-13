package agenda.exception;

/**
 * 相同用户异常。
 * 
 * <p>当尝试创建的会议发起人和被预约人是同一个用户时抛出此异常。
 * 该异常由业务逻辑层在参与者校验失败时抛出。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class SameUserException extends AgendaException {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 相同的用户名 */
    private final String username;
    
    /**
     * 构造函数，创建一个默认的相同用户异常实例。
     */
    public SameUserException() {
        super("发起人和被预约人不能是同一个用户");
        this.username = null;
    }
    
    /**
     * 构造函数，创建一个带有用户名的异常实例。
     * 
     * @param username 相同的用户名
     */
    public SameUserException(String username) {
        super("发起人和被预约人不能是同一个用户: " + username);
        this.username = username;
    }
    
    /**
     * 获取相同的用户名。
     * 
     * @return 相同的用户名，如果未指定则返回 null
     */
    public String getUsername() {
        return username;
    }
}