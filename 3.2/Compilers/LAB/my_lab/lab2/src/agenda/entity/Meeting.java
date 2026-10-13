package agenda.entity;

import java.io.Serializable;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 会议实体类，表示系统中的会议安排。
 * 
 * <p>会议实体包含发起人（sponsor）、被预约人（scheduled user）、
 * 开始时间、结束时间和会议标题等核心属性。会议标题作为会议的唯一标识符。</p>
 * 
 * <p>会议必须在两个已注册用户之间举行，且同一用户在同一时间段内不能有多个会议重叠。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03
 */
public class Meeting implements Serializable {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 日期时间格式化器，用于解析和格式化日期 */
    private static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
    
    /**
     * 会议发起人的用户名。
     * 发起人是创建会议的用户。
     */
    private final String sponsor;
    
    /**
     * 会议被预约人的用户名。
     * 被预约人是被邀请参加会议的用户。
     */
    private final String scheduledUser;
    
    /**
     * 会议开始时间。
     */
    private final Date start;
    
    /**
     * 会议结束时间。
     */
    private final Date end;
    
    /**
     * 会议标题，作为会议的唯一标识符。
     */
    private final String title;
    
    /**
     * 构造函数，创建一个新的会议实例。
     * 
     * @param sponsor 会议发起人的用户名，不能为 null 或空字符串
     * @param scheduledUser 会议被预约人的用户名，不能为 null 或空字符串
     * @param start 会议开始时间，不能为 null
     * @param end 会议结束时间，不能为 null
     * @param title 会议标题，不能为 null 或空字符串
     * @throws IllegalArgumentException 如果任何参数无效
     */
    public Meeting(String sponsor, String scheduledUser, Date start, Date end, String title) {
        if (sponsor == null || sponsor.trim().isEmpty()) {
            throw new IllegalArgumentException("发起人不能为空");
        }
        if (scheduledUser == null || scheduledUser.trim().isEmpty()) {
            throw new IllegalArgumentException("被预约人不能为空");
        }
        if (start == null) {
            throw new IllegalArgumentException("开始时间不能为空");
        }
        if (end == null) {
            throw new IllegalArgumentException("结束时间不能为空");
        }
        if (title == null || title.trim().isEmpty()) {
            throw new IllegalArgumentException("会议标题不能为空");
        }
        if (start.after(end)) {
            throw new IllegalArgumentException("开始时间不能晚于结束时间");
        }
        
        this.sponsor = sponsor.trim();
        this.scheduledUser = scheduledUser.trim();
        this.start = new Date(start.getTime()); // 防御性拷贝
        this.end = new Date(end.getTime()); // 防御性拷贝
        this.title = title.trim();
    }
    
    /**
     * 获取会议发起人的用户名。
     * 
     * @return 发起人用户名
     */
    public String getSponsor() {
        return sponsor;
    }
    
    /**
     * 获取会议被预约人的用户名。
     * 
     * @return 被预约人用户名
     */
    public String getScheduledUser() {
        return scheduledUser;
    }
    
    /**
     * 获取会议开始时间。
     * 
     * @return 开始时间的副本（防御性拷贝）
     */
    public Date getStart() {
        return new Date(start.getTime());
    }
    
    /**
     * 获取会议结束时间。
     * 
     * @return 结束时间的副本（防御性拷贝）
     */
    public Date getEnd() {
        return new Date(end.getTime());
    }
    
    /**
     * 获取会议标题。
     * 
     * @return 会议标题
     */
    public String getTitle() {
        return title;
    }
    
    /**
     * 检查指定用户是否参与此会议。
     * 用户可能是发起人或被预约人。
     * 
     * @param username 用户名
     * @return 如果用户参与此会议返回 true，否则返回 false
     */
    public boolean involvesUser(String username) {
        if (username == null) {
            return false;
        }
        return sponsor.equals(username) || scheduledUser.equals(username);
    }
    
    /**
     * 检查此会议是否与指定时间段存在重叠。
     * 
     * <p>两个时间段 [s1, e1] 和 [s2, e2] 存在重叠的条件是：
     * s1 &lt; e2 且 s2 &lt; e1</p>
     * 
     * @param otherStart 待检查的开始时间
     * @param otherEnd 待检查的结束时间
     * @return 如果存在时间重叠返回 true，否则返回 false
     */
    public boolean hasTimeConflict(Date otherStart, Date otherEnd) {
        if (otherStart == null || otherEnd == null) {
            return false;
        }
        // 两个时间段重叠的条件：start1 < end2 && start2 < end1
        return start.before(otherEnd) && otherStart.before(end);
    }
    
    /**
     * 检查此会议是否与另一个会议存在时间冲突。
     * 
     * @param other 另一个会议
     * @return 如果存在时间冲突返回 true，否则返回 false
     */
    public boolean hasTimeConflict(Meeting other) {
        if (other == null) {
            return false;
        }
        return hasTimeConflict(other.start, other.end);
    }
    
    /**
     * 检查此会议是否在指定时间范围内。
     * 
     * <p>会议在时间范围内是指会议与查询范围有交集</p>
     * 
     * @param rangeStart 范围开始时间
     * @param rangeEnd 范围结束时间
     * @return 如果会议在指定范围内返回 true，否则返回 false
     */
    public boolean isInRange(Date rangeStart, Date rangeEnd) {
        if (rangeStart == null || rangeEnd == null) {
            return false;
        }
        return hasTimeConflict(rangeStart, rangeEnd);
    }
    
    /**
     * 重写 equals 方法，基于会议标题判断两个会议是否相等。
     * 
     * @param obj 待比较的对象
     * @return 如果两个会议的标题相同返回 true，否则返回 false
     */
    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null || getClass() != obj.getClass()) {
            return false;
        }
        Meeting meeting = (Meeting) obj;
        return title.equals(meeting.title);
    }
    
    /**
     * 重写 hashCode 方法，基于会议标题生成哈希码。
     * 
     * @return 会议标题的哈希码
     */
    @Override
    public int hashCode() {
        return title.hashCode();
    }
    
    /**
     * 重写 toString 方法，返回会议的字符串表示。
     * 
     * @return 会议信息的字符串表示
     */
    @Override
    public String toString() {
        return "Meeting{" +
                "sponsor='" + sponsor + '\'' +
                ", scheduledUser='" + scheduledUser + '\'' +
                ", start=" + formatDate(start) +
                ", end=" + formatDate(end) +
                ", title='" + title + '\'' +
                '}';
    }
    
    /**
     * 格式化日期为字符串。
     * 
     * @param date 日期对象
     * @return 格式化后的日期字符串
     */
    private String formatDate(Date date) {
        return DATE_FORMAT.format(date);
    }
    
    /**
     * 获取日期格式化器。
     * 用于解析和格式化日期字符串。
     * 
     * @return 日期格式化器实例
     */
    public static SimpleDateFormat getDateFormat() {
        return DATE_FORMAT;
    }
}
