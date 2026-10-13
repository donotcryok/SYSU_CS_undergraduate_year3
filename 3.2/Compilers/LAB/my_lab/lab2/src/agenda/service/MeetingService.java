package agenda.service;

import agenda.entity.Meeting;
import agenda.entity.User;
import agenda.exception.AuthException;
import agenda.exception.MeetingNotFoundException;
import agenda.exception.SameUserException;
import agenda.exception.TimeConflictException;
import agenda.exception.UserNotFoundException;
import agenda.storage.Storage;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * 会议服务类，处理会议相关的业务逻辑。
 * 
 * <p>该类负责会议的创建、查询、删除、清除等核心业务操作，
 * 包括时间冲突检测、参与者验证等关键业务规则。</p>
 * 
 * <p>核心业务规则：
 * - 会议必须在两个已注册用户之间举行
 * - 同一用户在同一时间段内不能有多个会议重叠
 * - 会议标题作为会议的唯一标识</p>
 * 
 * <p>架构位置：业务逻辑层（Service Layer）
 * - 位于三层架构的中间层
 * - 依赖数据访问层（Storage）
 * - 不包含任何 UI 交互逻辑（无 System.out.println 或 Scanner）
 * - 通过抛出自定义异常向上传递业务校验失败</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class MeetingService {
    
    /** 数据访问层实例 */
    private final Storage storage;
    
    /** 用户服务实例 */
    private final UserService userService;
    
    /**
     * 构造函数，初始化会议服务。
     * 获取 Storage 单例实例和 UserService 实例。
     */
    public MeetingService() {
        this.storage = Storage.getInstance();
        this.userService = new UserService();
    }
    
    /**
     * 添加会议。
     * 
     * <p>创建新会议，需要满足以下条件：
     * - 发起人和被预约人都必须是已注册用户
     * - 发起人和被预约人不能是同一个用户
     * - 发起人和被预约人在指定时间段内都没有其他会议冲突
     * - 会议标题不能与现有会议重复</p>
     * 
     * @param sponsor 发起人用户名
     * @param password 发起人密码
     * @param scheduledUser 被预约人用户名
     * @param start 开始时间
     * @param end 结束时间
     * @param title 会议标题
     * @return 创建成功的会议对象
     * @throws UserNotFoundException 如果发起人或被预约人不存在
     * @throws AuthException 如果密码错误
     * @throws SameUserException 如果发起人和被预约人是同一个用户
     * @throws TimeConflictException 如果存在时间冲突
     */
    public Meeting addMeeting(String sponsor, String password, String scheduledUser,
                              Date start, Date end, String title)
            throws UserNotFoundException, AuthException, SameUserException, TimeConflictException {
        
        // 验证发起人登录
        userService.login(sponsor, password);
        
        // 验证被预约人是否存在
        if (!userService.userExists(scheduledUser)) {
            throw new UserNotFoundException(scheduledUser);
        }
        
        // 检查发起人和被预约人是否相同
        if (sponsor.equals(scheduledUser)) {
            throw new SameUserException(sponsor);
        }
        
        // 检查发起人时间冲突
        if (storage.hasTimeConflict(sponsor, start, end)) {
            throw new TimeConflictException(sponsor);
        }
        
        // 检查被预约人时间冲突
        if (storage.hasTimeConflict(scheduledUser, start, end)) {
            throw new TimeConflictException(scheduledUser);
        }
        
        // 创建会议
        Meeting meeting = new Meeting(sponsor, scheduledUser, start, end, title);
        storage.addMeeting(meeting);
        
        return meeting;
    }
    
    /**
     * 查询会议。
     * 
     * <p>查询指定用户在指定时间段内的所有会议。
     * 返回结果包含该用户作为发起人和被预约人的所有会议。</p>
     * 
     * @param username 用户名
     * @param password 密码
     * @param start 查询开始时间
     * @param end 查询结束时间
     * @return 符合条件的会议列表
     * @throws UserNotFoundException 如果用户不存在
     * @throws AuthException 如果密码错误
     */
    public List<Meeting> queryMeetings(String username, String password, Date start, Date end)
            throws UserNotFoundException, AuthException {
        
        // 验证用户登录
        userService.login(username, password);
        
        // 获取用户参与的所有会议
        List<Meeting> allMeetings = storage.getMeetingsByUser(username);
        
        // 筛选在指定时间范围内的会议
        List<Meeting> result = new ArrayList<>();
        for (Meeting meeting : allMeetings) {
            if (meeting.isInRange(start, end)) {
                result.add(meeting);
            }
        }
        
        return result;
    }
    
    /**
     * 删除会议。
     * 
     * <p>删除指定会议，只有发起人可以删除会议。</p>
     * 
     * @param username 用户名（发起人）
     * @param password 密码
     * @param meetingTitle 会议标题
     * @return 被删除的会议对象
     * @throws UserNotFoundException 如果用户不存在
     * @throws AuthException 如果密码错误
     * @throws MeetingNotFoundException 如果会议不存在或用户不是发起人
     */
    public Meeting deleteMeeting(String username, String password, String meetingTitle)
            throws UserNotFoundException, AuthException, MeetingNotFoundException {
        
        // 验证用户登录
        userService.login(username, password);
        
        // 查找会议
        Meeting meeting = storage.findMeetingByTitle(meetingTitle);
        if (meeting == null) {
            throw new MeetingNotFoundException(meetingTitle);
        }
        
        // 检查是否是发起人
        if (!meeting.getSponsor().equals(username)) {
            throw new MeetingNotFoundException(meetingTitle);
        }
        
        // 删除会议
        storage.removeMeeting(meetingTitle);
        
        return meeting;
    }
    
    /**
     * 清除用户发起的所有会议。
     * 
     * @param username 用户名
     * @param password 密码
     * @return 清除的会议数量
     * @throws UserNotFoundException 如果用户不存在
     * @throws AuthException 如果密码错误
     */
    public int clearMeetings(String username, String password)
            throws UserNotFoundException, AuthException {
        
        // 验证用户登录
        userService.login(username, password);
        
        // 清除用户发起的所有会议
        return storage.clearMeetingsBySponsor(username);
    }
    
    /**
     * 获取用户参与的所有会议。
     * 
     * @param username 用户名
     * @return 用户参与的会议列表
     */
    public List<Meeting> getMeetingsByUser(String username) {
        return storage.getMeetingsByUser(username);
    }
    
    /**
     * 获取用户发起的所有会议。
     * 
     * @param username 用户名
     * @return 用户发起的会议列表
     */
    public List<Meeting> getMeetingsBySponsor(String username) {
        return storage.getMeetingsBySponsor(username);
    }
}