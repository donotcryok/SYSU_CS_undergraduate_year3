package agenda.exception;

/**
 * 时间冲突异常。
 * 
 * <p>当尝试创建的会议与现有会议存在时间重叠时抛出此异常。
 * 该异常由业务逻辑层在时间冲突检测失败时抛出。</p>
 * 
 * <p>时间冲突检测算法：两个时间段 [s1, e1] 和 [s2, e2] 存在重叠的条件是：
 * s1 &lt; e2 且 s2 &lt; e1</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class TimeConflictException extends AgendaException {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 存在时间冲突的用户名 */
    private final String username;
    
    /** 冲突的会议标题（可选） */
    private final String conflictingMeeting;
    
    /**
     * 构造函数，创建一个默认的时间冲突异常实例。
     */
    public TimeConflictException() {
        super("会议时间冲突，该时间段已有其他会议安排");
        this.username = null;
        this.conflictingMeeting = null;
    }
    
    /**
     * 构造函数，创建一个带有冲突用户信息的异常实例。
     * 
     * @param username 存在时间冲突的用户名
     */
    public TimeConflictException(String username) {
        super("用户 " + username + " 在该时间段已有其他会议安排");
        this.username = username;
        this.conflictingMeeting = null;
    }
    
    /**
     * 构造函数，创建一个带有详细冲突信息的异常实例。
     * 
     * @param username 存在时间冲突的用户名
     * @param conflictingMeeting 冲突的会议标题
     */
    public TimeConflictException(String username, String conflictingMeeting) {
        super("用户 " + username + " 在该时间段已有会议: " + conflictingMeeting);
        this.username = username;
        this.conflictingMeeting = conflictingMeeting;
    }
    
    /**
     * 获取存在时间冲突的用户名。
     * 
     * @return 存在时间冲突的用户名，如果未指定则返回 null
     */
    public String getUsername() {
        return username;
    }
    
    /**
     * 获取冲突的会议标题。
     * 
     * @return 冲突的会议标题，如果未指定则返回 null
     */
    public String getConflictingMeeting() {
        return conflictingMeeting;
    }
}
