package agenda.exception;

/**
 * 会议未找到异常。
 * 
 * <p>当尝试删除或查询一个不存在的会议时抛出此异常。
 * 该异常由业务逻辑层在会议查询失败时抛出。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class MeetingNotFoundException extends AgendaException {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 未找到的会议标题 */
    private final String meetingTitle;
    
    /**
     * 构造函数，创建一个带有会议标题的异常实例。
     * 
     * @param meetingTitle 未找到的会议标题
     */
    public MeetingNotFoundException(String meetingTitle) {
        super("会议不存在: " + meetingTitle);
        this.meetingTitle = meetingTitle;
    }
    
    /**
     * 获取未找到的会议标题。
     * 
     * @return 未找到的会议标题
     */
    public String getMeetingTitle() {
        return meetingTitle;
    }
}