package agenda.ui;

import agenda.entity.Meeting;
import agenda.exception.AuthException;
import agenda.exception.InvalidTimeFormatException;
import agenda.exception.MeetingNotFoundException;
import agenda.exception.SameUserException;
import agenda.exception.TimeConflictException;
import agenda.exception.UserNotFoundException;
import agenda.service.MeetingService;

import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 添加会议命令（Add Command）。
 * 
 * <p>处理添加会议命令，格式为：add [userName] [password] [other] [start] [end] [title]</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）
 * - 调用 MeetingService 处理业务逻辑
 * - 捕获异常并格式化输出</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class AddCommand implements Command {
    
    /** 会议服务实例 */
    private final MeetingService meetingService;
    
    /** 日期格式化器 */
    private static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
    
    /**
     * 构造函数，初始化添加会议命令。
     */
    public AddCommand() {
        this.meetingService = new MeetingService();
    }
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称 "add"
     */
    @Override
    public String getName() {
        return "add";
    }
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明
     */
    @Override
    public String getUsage() {
        return "add [userName] [password] [other] [start] [end] [title] - 添加会议\n" +
               "  时间格式: yyyy-MM-dd HH:mm:ss";
    }
    
    /**
     * 执行添加会议命令。
     * 
     * @param args 命令参数数组
     * @return 执行结果消息
     */
    @Override
    public String execute(String[] args) {
        // 检查参数数量
        if (args == null || args.length < 6) {
            return "错误: 参数不足\n用法: " + getUsage();
        }
        
        String username = args[0];
        String password = args[1];
        String other = args[2];
        String startStr = args[3];
        String endStr = args[4];
        String title = args[5];
        
        try {
            // 解析时间
            Date start = parseDate(startStr);
            Date end = parseDate(endStr);
            
            // 添加会议
            Meeting meeting = meetingService.addMeeting(username, password, other, start, end, title);
            return "会议创建成功: " + meeting.getTitle();
        } catch (InvalidTimeFormatException e) {
            return "错误: " + e.getMessage();
        } catch (UserNotFoundException e) {
            return "错误: " + e.getMessage();
        } catch (AuthException e) {
            return "错误: " + e.getMessage();
        } catch (SameUserException e) {
            return "错误: " + e.getMessage();
        } catch (TimeConflictException e) {
            return "错误: " + e.getMessage();
        }
    }
    
    /**
     * 解析日期字符串。
     * 
     * @param dateStr 日期字符串，格式为 yyyy-MM-dd HH:mm:ss
     * @return 解析后的 Date 对象
     * @throws InvalidTimeFormatException 如果日期格式错误
     */
    private Date parseDate(String dateStr) throws InvalidTimeFormatException {
        try {
            return DATE_FORMAT.parse(dateStr);
        } catch (java.text.ParseException e) {
            throw new InvalidTimeFormatException(dateStr);
        }
    }
}