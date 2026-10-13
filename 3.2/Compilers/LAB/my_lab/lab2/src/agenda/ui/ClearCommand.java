package agenda.ui;

import agenda.exception.AuthException;
import agenda.exception.UserNotFoundException;
import agenda.service.MeetingService;

/**
 * 清除会议命令（Clear Command）。
 * 
 * <p>处理清除会议命令，格式为：clear [userName] [password]</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）
 * - 调用 MeetingService 处理业务逻辑
 * - 捕获异常并格式化输出</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class ClearCommand implements Command {
    
    /** 会议服务实例 */
    private final MeetingService meetingService;
    
    /**
     * 构造函数，初始化清除会议命令。
     */
    public ClearCommand() {
        this.meetingService = new MeetingService();
    }
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称 "clear"
     */
    @Override
    public String getName() {
        return "clear";
    }
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明
     */
    @Override
    public String getUsage() {
        return "clear [userName] [password] - 清除用户发起的所有会议";
    }
    
    /**
     * 执行清除会议命令。
     * 
     * @param args 命令参数数组
     * @return 执行结果消息
     */
    @Override
    public String execute(String[] args) {
        // 检查参数数量
        if (args == null || args.length < 2) {
            return "错误: 参数不足\n用法: " + getUsage();
        }
        
        String username = args[0];
        String password = args[1];
        
        try {
            int count = meetingService.clearMeetings(username, password);
            return "已清除 " + count + " 个会议";
        } catch (UserNotFoundException e) {
            return "错误: " + e.getMessage();
        } catch (AuthException e) {
            return "错误: " + e.getMessage();
        }
    }
}