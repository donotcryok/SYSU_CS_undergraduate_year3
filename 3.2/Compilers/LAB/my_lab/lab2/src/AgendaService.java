import agenda.ui.CommandParser;
import java.util.Scanner;

/**
 * Agenda 议程管理系统主程序。
 * 
 * <p>这是系统的主入口点，负责初始化系统并启动命令行交互循环。
 * 系统采用分层架构设计，表示层通过 CommandParser 解析用户输入，
 * 并调用业务逻辑层处理具体业务。</p>
 * 
 * <p>系统架构：
 * - 表示层（Presentation Tier）：AgendaService, CommandParser, Command 系列
 * - 业务逻辑层（Business Logic Tier）：UserService, MeetingService, AgendaDataService</p>
 * 
 * <p>设计模式应用：
 * - 单例模式：AgendaDataService 管理数据源
 * - 命令模式：Command 接口封装命令处理
 * - 工厂模式：CommandFactory 创建命令对象</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03
 */
public class AgendaService {
    
    /** 命令解析器实例 */
    private final CommandParser commandParser;
    
    /** 扫描器实例，用于读取用户输入 */
    private final Scanner scanner;
    
    /** 系统提示符 */
    private static final String PROMPT = "$ ";
    
    /** 系统欢迎信息 */
    private static final String WELCOME_MESSAGE = 
        "===========================================================\n" +
        "    Agenda 议程管理系统\n" +
        "===========================================================\n" +
        "输入 'help' 查看可用命令，输入 'quit' 退出系统\n";
    
    /**
     * 构造函数，初始化 Agenda 服务。
     */
    public AgendaService() {
        this.commandParser = new CommandParser();
        this.scanner = new Scanner(System.in);
    }
    
    /**
     * 启动系统，进入命令行交互循环。
     */
    public void start() {
        // 显示欢迎信息
        System.out.println(WELCOME_MESSAGE);
        
        // 显示可用命令
        System.out.println(commandParser.getCommandFactory().getAvailableCommands());
        System.out.println();
        
        // 进入交互循环
        while (true) {
            // 显示提示符
            System.out.print(PROMPT);
            
            // 读取用户输入
            String input = scanner.nextLine();
            
            // 解析并执行命令
            String result = commandParser.parseAndExecute(input);
            
            // 输出结果
            System.out.println(result);
            
            // 检查是否应该退出
            if (commandParser.shouldQuit()) {
                break;
            }
        }
        
        // 关闭扫描器
        scanner.close();
    }
    
    /**
     * 程序主入口。
     * 
     * @param args 命令行参数
     */
    public static void main(String[] args) {
        AgendaService agendaService = new AgendaService();
        agendaService.start();
    }
}