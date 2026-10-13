package agenda.ui;

/**
 * 退出命令（Quit Command）。
 * 
 * <p>处理退出系统命令，格式为：quit</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class QuitCommand implements Command {
    
    /** 退出标志 */
    private boolean shouldQuit = false;
    
    /**
     * 构造函数，初始化退出命令。
     */
    public QuitCommand() {
        this.shouldQuit = false;
    }
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称 "quit"
     */
    @Override
    public String getName() {
        return "quit";
    }
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明
     */
    @Override
    public String getUsage() {
        return "quit - 退出系统";
    }
    
    /**
     * 执行退出命令。
     * 
     * @param args 命令参数数组（退出命令不需要参数）
     * @return 退出消息
     */
    @Override
    public String execute(String[] args) {
        shouldQuit = true;
        return "感谢使用 Agenda 系统，再见！";
    }
    
    /**
     * 检查是否应该退出系统。
     * 
     * @return 如果应该退出返回 true，否则返回 false
     */
    public boolean shouldQuit() {
        return shouldQuit;
    }
    
    /**
     * 重置退出标志。
     * 用于批处理命令执行后重置状态。
     */
    public void resetQuitFlag() {
        shouldQuit = false;
    }
}