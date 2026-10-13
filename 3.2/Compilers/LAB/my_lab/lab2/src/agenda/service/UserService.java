package agenda.service;

import agenda.entity.User;
import agenda.exception.AuthException;
import agenda.exception.UserAlreadyExistsException;
import agenda.exception.UserNotFoundException;
import agenda.storage.Storage;

/**
 * 用户服务类，处理用户相关的业务逻辑。
 * 
 * <p>该类负责用户注册、登录验证、用户查询等核心业务操作。
 * 所有操作通过 Storage 单例进行数据访问。</p>
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
public class UserService {
    
    /** 数据访问层实例 */
    private final Storage storage;
    
    /**
     * 构造函数，初始化用户服务。
     * 获取 Storage 单例实例。
     */
    public UserService() {
        this.storage = Storage.getInstance();
    }
    
    /**
     * 用户注册。
     * 
     * <p>注册新用户，用户名必须唯一。如果用户名已存在，
     * 抛出 UserAlreadyExistsException 异常。</p>
     * 
     * @param username 用户名
     * @param password 密码
     * @return 注册成功的用户对象
     * @throws UserAlreadyExistsException 如果用户名已存在
     */
    public User register(String username, String password) throws UserAlreadyExistsException {
        // 检查用户是否已存在
        if (storage.userExists(username)) {
            throw new UserAlreadyExistsException(username);
        }
        
        // 创建新用户并添加到数据存储
        User user = new User(username, password);
        storage.addUser(user);
        
        return user;
    }
    
    /**
     * 用户登录验证。
     * 
     * <p>验证用户名和密码是否匹配。如果用户不存在，
     * 抛出 UserNotFoundException 异常；如果密码错误，
     * 抛出 AuthException 异常。</p>
     * 
     * @param username 用户名
     * @param password 密码
     * @return 验证成功的用户对象
     * @throws UserNotFoundException 如果用户不存在
     * @throws AuthException 如果密码错误
     */
    public User login(String username, String password) 
            throws UserNotFoundException, AuthException {
        // 查找用户
        User user = storage.findUserByUsername(username);
        if (user == null) {
            throw new UserNotFoundException(username);
        }
        
        // 验证密码
        if (!user.validatePassword(password)) {
            throw new AuthException(username);
        }
        
        return user;
    }
    
    /**
     * 检查用户是否存在。
     * 
     * @param username 用户名
     * @return 如果用户存在返回 true，否则返回 false
     */
    public boolean userExists(String username) {
        return storage.userExists(username);
    }
    
    /**
     * 根据用户名查找用户。
     * 
     * @param username 用户名
     * @return 用户对象，如果不存在返回 null
     */
    public User findUser(String username) {
        return storage.findUserByUsername(username);
    }
}