package agenda.ui;

import agenda.entity.Meeting;
import agenda.exception.AuthException;
import agenda.exception.InvalidTimeFormatException;
import agenda.exception.UserNotFoundException;
import agenda.service.MeetingService;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

/**
 * 查询会议命令（Query Command）。
 * 
 * <p>处理查询会议命令，格式为：query [userName] [password] [start] [end]</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）
 * - 调用 MeetingService 处理业务逻辑
 * - 捕获异常并格式化输出</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class QueryCommand implements Command {
    
    /** 会议服务实例 */
    private final MeetingService meetingService;
    
    /** 日期格式化器 */
    private static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
    
    /**
     * 构造函数，初始化查询会议命令。
     */
    public QueryCommand() {
        this.meetingService = new MeetingService();
    }
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称 "query"
     */
    @Override
    public String getName() {
        return "query";
    }
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明
     */
    @Override
    public String getUsage() {
        return "query [userName] [password] [start] [end] - 查询会议\n" +
               "  时间格式: yyyy-MM-dd HH:mm:ss";
    }
    
    /**
     * 执行查询会议命令。
     * 
     * @param args 命令参数数组
     * @return 执行结果消息
     */
    @Override
    public String execute(String[] args) {
        // 检查参数数量
        if (args == null || args.length < 4) {
            return "错误: 参数不足\n用法: " + getUsage();
        }
        
        String username = args[0];
        String password = args[1];
        String startStr = args[2];
        String endStr = args[3];
        
        try {
            // 解析时间
            Date start = parseDate(startStr);
            Date end = parseDate(endStr);
            
            // 查询会议
            List<Meeting> meetings = meetingService.queryMeetings(username, password, start, end);
            
            // 构建返回信息
            if (meetings.isEmpty()) {
                return "在该时间段内没有会议安排";
            }
            
            StringBuilder sb = new StringBuilder();
            sb.append("查询结果 (共 ").append(meetings.size()).append(" 个会议):\n");
            for (Meeting meeting : meetings) {
                sb.append(formatMeetingInfo(meeting, username)).append("\n");
            }
            return sb.toString().trim();
        } catch (InvalidTimeFormatException e) {
            return "错误: " + e.getMessage();
        } catch (UserNotFoundException e) {
            return "错误: " + e.getMessage();
        } catch (AuthException e) {
            return "错误: " + e.getMessage();
        }
    }
    
    /**
     * 解析日期字符串。
     * 
     * @param dateStr 日期字符串
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
    
    /**
     * 格式化会议信息。
     * 
     * @param meeting 会议对象
     * @param currentUser 当前用户
     * @return 格式化后的会议信息
     */
    private String formatMeetingInfo(Meeting meeting, String currentUser) {
        String other;
        if (meeting.getSponsor().equals(currentUser)) {
            other = meeting.getScheduledUser();
        } else {
            other = meeting.getSponsor();
        }
        
        return String.format("标题: %s | 时间: %s - %s | 另一方: %s",
                meeting.getTitle(),
                DATE_FORMAT.format(meeting.getStart()),
                DATE_FORMAT.format(meeting.getEnd()),
                other);
    }
}