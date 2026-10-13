package agenda.ui;

import agenda.exception.AuthException;
import agenda.exception.MeetingNotFoundException;
import agenda.exception.UserNotFoundException;
import agenda.service.MeetingService;

/**
 * 删除会议命令（Delete Command）。
 * 
 * <p>处理删除会议命令，格式为：delete [userName] [password] [meetingId]</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）
 * - 调用 MeetingService 处理业务逻辑
 * - 捕获异常并格式化输出</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class DeleteCommand implements Command {
    
    /** 会议服务实例 */
    private final MeetingService meetingService;
    
    /**
     * 构造函数，初始化删除会议命令。
     */
    public DeleteCommand() {
        this.meetingService = new MeetingService();
    }
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称 "delete"
     */
    @Override
    public String getName() {
        return "delete";
    }
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明
     */
    @Override
    public String getUsage() {
        return "delete [userName] [password] [meetingId] - 删除会议\n" +
               "  meetingId 为会议标题";
    }
    
    /**
     * 执行删除会议命令。
     * 
     * @param args 命令参数数组
     * @return 执行结果消息
     */
    @Override
    public String execute(String[] args) {
        // 检查参数数量
        if (args == null || args.length < 3) {
            return "错误: 参数不足\n用法: " + getUsage();
        }
        
        String username = args[0];
        String password = args[1];
        String meetingId = args[2];
        
        try {
            meetingService.deleteMeeting(username, password, meetingId);
            return "会议删除成功: " + meetingId;
        } catch (UserNotFoundException e) {
            return "错误: " + e.getMessage();
        } catch (AuthException e) {
            return "错误: " + e.getMessage();
        } catch (MeetingNotFoundException e) {
            return "错误: " + e.getMessage();
        }
    }
}