package agenda.ui;

import agenda.entity.User;
import agenda.exception.UserAlreadyExistsException;
import agenda.service.UserService;

/**
 * 注册命令（Register Command）。
 * 
 * <p>处理用户注册命令，格式为：register [userName] [password]</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）
 * - 调用 UserService 处理业务逻辑
 * - 捕获异常并格式化输出</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class RegisterCommand implements Command {
    
    /** 用户服务实例 */
    private final UserService userService;
    
    /**
     * 构造函数，初始化注册命令。
     */
    public RegisterCommand() {
        this.userService = new UserService();
    }
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称 "register"
     */
    @Override
    public String getName() {
        return "register";
    }
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明
     */
    @Override
    public String getUsage() {
        return "register [userName] [password] - 注册新用户";
    }
    
    /**
     * 执行注册命令。
     * 
     * @param args 命令参数数组，args[0] 为用户名，args[1] 为密码
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
            User user = userService.register(username, password);
            return "用户注册成功: " + user.getUsername();
        } catch (UserAlreadyExistsException e) {
            return "错误: " + e.getMessage();
        }
    }
}