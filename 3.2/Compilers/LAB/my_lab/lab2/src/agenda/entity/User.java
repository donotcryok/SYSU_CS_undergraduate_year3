package agenda.entity;

import java.io.Serializable;

/**
 * 用户实体类，表示系统中的注册用户。
 * 
 * <p>用户实体包含用户名和密码两个核心属性。用户名在系统中必须唯一，
 * 作为用户的唯一标识符。</p>
 * 
 * <p>本类实现了 {@link Serializable} 接口，支持序列化操作，
 * 便于未来扩展数据持久化功能。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03
 */
public class User implements Serializable {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /**
     * 用户名，作为用户的唯一标识符。
     * 用户名在系统中必须唯一，且大小写敏感。
     */
    private final String username;
    
    /**
     * 用户密码，用于身份验证。
     * 密码大小写敏感。
     */
    private String password;
    
    /**
     * 构造函数，创建一个新的用户实例。
     * 
     * @param username 用户名，不能为 null 或空字符串
     * @param password 用户密码，不能为 null 或空字符串
     * @throws IllegalArgumentException 如果用户名或密码为 null 或空字符串
     */
    public User(String username, String password) {
        if (username == null || username.trim().isEmpty()) {
            throw new IllegalArgumentException("用户名不能为空");
        }
        if (password == null || password.trim().isEmpty()) {
            throw new IllegalArgumentException("密码不能为空");
        }
        this.username = username.trim();
        this.password = password;
    }
    
    /**
     * 获取用户名。
     * 
     * @return 用户名字符串
     */
    public String getUsername() {
        return username;
    }
    
    /**
     * 获取用户密码。
     * 
     * @return 密码字符串
     */
    public String getPassword() {
        return password;
    }
    
    /**
     * 设置用户密码。
     * 
     * @param password 新密码，不能为 null 或空字符串
     * @throws IllegalArgumentException 如果密码为 null 或空字符串
     */
    public void setPassword(String password) {
        if (password == null || password.trim().isEmpty()) {
            throw new IllegalArgumentException("密码不能为空");
        }
        this.password = password;
    }
    
    /**
     * 验证给定的密码是否与用户密码匹配。
     * 
     * @param password 待验证的密码
     * @return 如果密码匹配返回 true，否则返回 false
     */
    public boolean validatePassword(String password) {
        if (password == null) {
            return false;
        }
        return this.password.equals(password);
    }
    
    /**
     * 重写 equals 方法，基于用户名判断两个用户是否相等。
     * 
     * @param obj 待比较的对象
     * @return 如果两个用户的用户名相同返回 true，否则返回 false
     */
    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null || getClass() != obj.getClass()) {
            return false;
        }
        User user = (User) obj;
        return username.equals(user.username);
    }
    
    /**
     * 重写 hashCode 方法，基于用户名生成哈希码。
     * 
     * @return 用户名的哈希码
     */
    @Override
    public int hashCode() {
        return username.hashCode();
    }
    
    /**
     * 重写 toString 方法，返回用户的字符串表示。
     * 
     * @return 用户信息的字符串表示（不包含密码，保护用户隐私）
     */
    @Override
    public String toString() {
        return "User{username='" + username + "'}";
    }
}
