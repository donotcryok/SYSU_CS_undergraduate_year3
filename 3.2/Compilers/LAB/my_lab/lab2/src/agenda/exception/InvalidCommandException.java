package agenda.exception;

/**
 * 命令格式错误异常。
 * 
 * <p>当用户输入的命令格式不正确或参数数量不匹配时抛出此异常。
 * 该异常由表示层在解析命令失败时抛出。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class InvalidCommandException extends AgendaException {
    
    /** 序列化版本号 */
    private static final long serialVersionUID = 1L;
    
    /** 错误的命令名称 */
    private final String commandName;
    
    /** 预期参数数量 */
    private final int expectedArgs;
    
    /** 实际参数数量 */
    private final int actualArgs;
    
    /**
     * 构造函数，创建一个默认的命令格式错误异常实例。
     */
    public InvalidCommandException() {
        super("命令格式错误，请输入正确的命令格式");
        this.commandName = null;
        this.expectedArgs = -1;
        this.actualArgs = -1;
    }
    
    /**
     * 构造函数，创建一个带有命令名称的异常实例。
     * 
     * @param commandName 错误的命令名称
     */
    public InvalidCommandException(String commandName) {
        super("未知命令: " + commandName);
        this.commandName = commandName;
        this.expectedArgs = -1;
        this.actualArgs = -1;
    }
    
    /**
     * 构造函数，创建一个带有命令名称和参数数量的异常实例。
     * 
     * @param commandName 命令名称
     * @param expected 预期参数数量
     * @param actual 实际参数数量
     */
    public InvalidCommandException(String commandName, int expected, int actual) {
        super("命令 " + commandName + " 参数数量错误，预期 " + expected + " 个，实际 " + actual + " 个");
        this.commandName = commandName;
        this.expectedArgs = expected;
        this.actualArgs = actual;
    }
    
    /**
     * 获取错误的命令名称。
     * 
     * @return 错误的命令名称，如果未指定则返回 null
     */
    public String getCommandName() {
        return commandName;
    }
    
    /**
     * 获取预期参数数量。
     * 
     * @return 预期参数数量，如果未指定则返回 -1
     */
    public int getExpectedArgs() {
        return expectedArgs;
    }
    
    /**
     * 获取实际参数数量。
     * 
     * @return 实际参数数量，如果未指定则返回 -1
     */
    public int getActualArgs() {
        return actualArgs;
    }
}