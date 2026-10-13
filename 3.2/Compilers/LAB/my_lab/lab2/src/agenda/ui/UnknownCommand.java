package agenda.ui;

/**
 * 未知命令（Unknown Command）。
 * 
 * <p>处理无法识别的命令，提供错误提示。</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class UnknownCommand implements Command {
    
    /** 输入的命令名称 */
    private final String inputCommand;
    
    /**
     * 构造函数，初始化未知命令。
     * 
     * @param inputCommand 用户输入的命令名称
     */
    public UnknownCommand(String inputCommand) {
        this.inputCommand = inputCommand;
    }
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称 "unknown"
     */
    @Override
    public String getName() {
        return "unknown";
    }
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明
     */
    @Override
    public String getUsage() {
        return "可用命令: register, add, query, delete, clear, batch, quit";
    }
    
    /**
     * 执行未知命令。
     * 
     * @param args 命令参数数组
     * @return 错误提示消息
     */
    @Override
    public String execute(String[] args) {
        return "错误: 未知命令 '" + inputCommand + "'\n" + getUsage();
    }
}