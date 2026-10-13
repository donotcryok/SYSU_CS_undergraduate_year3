package agenda.service;

import agenda.entity.Meeting;
import agenda.entity.User;
import java.util.ArrayList;
import java.util.List;

/**
 * Agenda 数据管理服务（单例模式）。
 * 
 * <p>该类采用单例模式设计，确保整个应用程序中只有一个数据存储实例。
 * 负责管理系统中的所有用户和会议数据，提供数据的增删查改操作。</p>
 * 
 * <p>设计模式：单例模式（Singleton Pattern）
 * - 私有静态实例变量
 * - 私有构造函数
 * - 公有静态获取方法（线程安全）</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class AgendaDataService {
    
    /** 单例实例 */
    private static AgendaDataService instance;
    
    /** 用户列表 */
    private final List<User> users;
    
    /** 会议列表 */
    private final List<Meeting> meetings;
    
    /**
     * 私有构造函数，防止外部直接创建实例。
     * 初始化用户列表和会议列表。
     */
    private AgendaDataService() {
        users = new ArrayList<>();
        meetings = new ArrayList<>();
    }
    
    /**
     * 获取单例实例（线程安全）。
     * 
     * @return AgendaDataService 的唯一实例
     */
    public static synchronized AgendaDataService getInstance() {
        if (instance == null) {
            instance = new AgendaDataService();
        }
        return instance;
    }
    
    // ==================== 用户管理操作 ====================
    
    /**
     * 获取所有用户列表。
     * 
     * @return 用户列表
     */
    public List<User> getUsers() {
        return new ArrayList<>(users); // 返回副本，保护原始数据
    }
    
    /**
     * 根据用户名查找用户。
     * 
     * @param username 用户名
     * @return 用户对象，如果不存在返回 null
     */
    public User findUserByUsername(String username) {
        for (User user : users) {
            if (user.getUsername().equals(username)) {
                return user;
            }
        }
        return null;
    }
    
    /**
     * 检查用户是否存在。
     * 
     * @param username 用户名
     * @return 如果用户存在返回 true，否则返回 false
     */
    public boolean userExists(String username) {
        return findUserByUsername(username) != null;
    }
    
    /**
     * 添加新用户。
     * 
     * @param user 用户对象
     * @return 如果添加成功返回 true，如果用户已存在返回 false
     */
    public boolean addUser(User user) {
        if (userExists(user.getUsername())) {
            return false;
        }
        users.add(user);
        return true;
    }
    
    // ==================== 会议管理操作 ====================
    
    /**
     * 获取所有会议列表。
     * 
     * @return 会议列表
     */
    public List<Meeting> getMeetings() {
        return new ArrayList<>(meetings); // 返回副本，保护原始数据
    }
    
    /**
     * 根据标题查找会议。
     * 
     * @param title 会议标题
     * @return 会议对象，如果不存在返回 null
     */
    public Meeting findMeetingByTitle(String title) {
        for (Meeting meeting : meetings) {
            if (meeting.getTitle().equals(title)) {
                return meeting;
            }
        }
        return null;
    }
    
    /**
     * 检查会议是否存在。
     * 
     * @param title 会议标题
     * @return 如果会议存在返回 true，否则返回 false
     */
    public boolean meetingExists(String title) {
        return findMeetingByTitle(title) != null;
    }
    
    /**
     * 添加新会议。
     * 
     * @param meeting 会议对象
     * @return 如果添加成功返回 true，如果会议已存在返回 false
     */
    public boolean addMeeting(Meeting meeting) {
        if (meetingExists(meeting.getTitle())) {
            return false;
        }
        meetings.add(meeting);
        return true;
    }
    
    /**
     * 删除会议。
     * 
     * @param title 会议标题
     * @return 如果删除成功返回 true，如果会议不存在返回 false
     */
    public boolean removeMeeting(String title) {
        Meeting meeting = findMeetingByTitle(title);
        if (meeting != null) {
            meetings.remove(meeting);
            return true;
        }
        return false;
    }
    
    /**
     * 获取指定用户参与的所有会议（作为发起人或被预约人）。
     * 
     * @param username 用户名
     * @return 用户参与的会议列表
     */
    public List<Meeting> getMeetingsByUser(String username) {
        List<Meeting> result = new ArrayList<>();
        for (Meeting meeting : meetings) {
            if (meeting.involvesUser(username)) {
                result.add(meeting);
            }
        }
        return result;
    }
    
    /**
     * 获取指定用户作为发起人的所有会议。
     * 
     * @param username 用户名
     * @return 用户发起的会议列表
     */
    public List<Meeting> getMeetingsBySponsor(String username) {
        List<Meeting> result = new ArrayList<>();
        for (Meeting meeting : meetings) {
            if (meeting.getSponsor().equals(username)) {
                result.add(meeting);
            }
        }
        return result;
    }
    
    /**
     * 清除指定用户发起的所有会议。
     * 
     * @param username 用户名
     * @return 清除的会议数量
     */
    public int clearMeetingsBySponsor(String username) {
        int count = 0;
        List<Meeting> toRemove = new ArrayList<>();
        for (Meeting meeting : meetings) {
            if (meeting.getSponsor().equals(username)) {
                toRemove.add(meeting);
                count++;
            }
        }
        meetings.removeAll(toRemove);
        return count;
    }
    
    /**
     * 检查指定用户在指定时间段是否有会议冲突。
     * 
     * @param username 用户名
     * @param start 开始时间
     * @param end 结束时间
     * @return 如果存在冲突返回 true，否则返回 false
     */
    public boolean hasTimeConflict(String username, java.util.Date start, java.util.Date end) {
        for (Meeting meeting : meetings) {
            if (meeting.involvesUser(username)) {
                if (meeting.hasTimeConflict(start, end)) {
                    return true;
                }
            }
        }
        return false;
    }
    
    /**
     * 检查指定用户在指定时间段是否有会议冲突（排除指定会议）。
     * 用于更新会议时排除自身。
     * 
     * @param username 用户名
     * @param start 开始时间
     * @param end 结束时间
     * @param excludeTitle 排除的会议标题
     * @return 如果存在冲突返回 true，否则返回 false
     */
    public boolean hasTimeConflictExclude(String username, java.util.Date start, java.util.Date end, String excludeTitle) {
        for (Meeting meeting : meetings) {
            if (!meeting.getTitle().equals(excludeTitle)) {
                if (meeting.involvesUser(username)) {
                    if (meeting.hasTimeConflict(start, end)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }
    
    /**
     * 重置所有数据（用于测试）。
     */
    public void reset() {
        users.clear();
        meetings.clear();
    }
}