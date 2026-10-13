package agenda.exception;

/**
 * 会议时间冲突异常。
 * 
 * <p>当尝试创建的会议与现有会议存在时间重叠时抛出此异常。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class MeetingConflictException extends AgendaException {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * 构造函数，创建一个默认的会议冲突异常实例。
     */
    public MeetingConflictException() {
        super("会议时间冲突，该时间段已有其他会议安排");
    }
    
    /**
     * 构造函数，创建一个带有冲突用户信息的异常实例。
     * 
     * @param username 存在时间冲突的用户名
     */
    public MeetingConflictException(String username) {
        super("用户 " + username + " 在该时间段已有其他会议安排");
    }
    
    /**
     * 构造函数，创建一个带有详细冲突信息的异常实例。
     * 
     * @param username 存在时间冲突的用户名
     * @param conflictingMeeting 冲突的会议标题
     */
    public MeetingConflictException(String username, String conflictingMeeting) {
        super("用户 " + username + " 在该时间段已有会议: " + conflictingMeeting);
    }
}