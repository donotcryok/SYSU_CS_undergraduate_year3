package agenda.ui;

/**
 * 命令工厂类（工厂模式）。
 * 
 * <p>该类采用工厂模式设计，根据命令名称动态创建对应的命令对象。
 * 将命令对象的创建逻辑集中管理，客户端无需知道具体命令类的创建细节。</p>
 * 
 * <p>设计模式：工厂模式（Factory Pattern）
 * - 集中管理对象的创建逻辑
 * - 客户端通过工厂获取对象，无需直接创建
 * - 便于添加新的命令类型</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class CommandFactory {
    
    /** 退出命令实例（需要保持状态） */
    private final QuitCommand quitCommand;
    
    /**
     * 构造函数，初始化命令工厂。
     */
    public CommandFactory() {
        this.quitCommand = new QuitCommand();
    }
    
    /**
     * 根据命令名称创建命令对象。
     * 
     * @param commandName 命令名称（大小写不敏感）
     * @return 对应的命令对象
     */
    public Command createCommand(String commandName) {
        if (commandName == null || commandName.trim().isEmpty()) {
            return new UnknownCommand("");
        }
        
        // 命令名称大小写不敏感
        String name = commandName.toLowerCase().trim();
        
        switch (name) {
            case "register":
                return new RegisterCommand();
            case "add":
                return new AddCommand();
            case "query":
                return new QueryCommand();
            case "delete":
                return new DeleteCommand();
            case "clear":
                return new ClearCommand();
            case "batch":
                return new BatchCommand();
            case "quit":
            case "exit":
                return quitCommand;
            default:
                return new UnknownCommand(commandName);
        }
    }
    
    /**
     * 获取退出命令实例。
     * 用于检查是否应该退出系统。
     * 
     * @return 退出命令实例
     */
    public QuitCommand getQuitCommand() {
        return quitCommand;
    }
    
    /**
     * 获取所有可用命令的列表。
     * 
     * @return 可用命令列表
     */
    public String getAvailableCommands() {
        return "可用命令:\n" +
               "  register [userName] [password] - 注册新用户\n" +
               "  add [userName] [password] [other] [start] [end] [title] - 添加会议\n" +
               "  query [userName] [password] [start] [end] - 查询会议\n" +
               "  delete [userName] [password] [meetingId] - 删除会议\n" +
               "  clear [userName] [password] - 清除会议\n" +
               "  batch [fileName] - 执行批处理文件\n" +
               "  quit - 退出系统\n" +
               "注意: 时间格式为 yyyy-MM-dd HH:mm:ss";
    }
}