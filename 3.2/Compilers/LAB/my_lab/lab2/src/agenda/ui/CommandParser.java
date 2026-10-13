package agenda.ui;

/**
 * 命令解析器类。
 * 
 * <p>负责将用户输入的字符串解析为命令对象并执行。
 * 处理命令行输入的解析、参数提取和命令调用。</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class CommandParser {
    
    /** 命令工厂实例 */
    private final CommandFactory commandFactory;
    
    /**
     * 构造函数，初始化命令解析器。
     */
    public CommandParser() {
        this.commandFactory = new CommandFactory();
    }
    
    /**
     * 解析并执行用户输入的命令。
     * 
     * @param input 用户输入的命令字符串
     * @return 命令执行结果
     */
    public String parseAndExecute(String input) {
        if (input == null || input.trim().isEmpty()) {
            return "错误: 请输入命令";
        }
        
        // 去除提示符 $
        String trimmedInput = input.trim();
        if (trimmedInput.startsWith("$")) {
            trimmedInput = trimmedInput.substring(1).trim();
        }
        
        // 分割命令和参数
        String[] parts = parseCommandParts(trimmedInput);
        
        if (parts.length == 0) {
            return "错误: 请输入命令";
        }
        
        // 获取命令名称和参数
        String commandName = parts[0];
        String[] args = new String[parts.length - 1];
        for (int i = 1; i < parts.length; i++) {
            args[i - 1] = parts[i];
        }
        
        // 创建并执行命令
        Command command = commandFactory.createCommand(commandName);
        return command.execute(args);
    }
    
    /**
     * 解析命令字符串为部分数组。
     * 支持空格分隔的参数，时间参数中的空格会被正确处理。
     * 
     * @param input 命令字符串
     * @return 命令部分数组
     */
    private String[] parseCommandParts(String input) {
        // 处理时间参数中的空格（时间格式 yyyy-MM-dd HH:mm:ss）
        // 使用正则表达式匹配，将时间作为一个整体参数
        java.util.List<String> parts = new java.util.ArrayList<>();
        
        // 正则表达式：匹配时间格式 yyyy-MM-dd HH:mm:ss 或普通参数
        java.util.regex.Pattern timePattern = java.util.regex.Pattern.compile(
            "(\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2})|(\\S+)"
        );
        
        java.util.regex.Matcher matcher = timePattern.matcher(input);
        while (matcher.find()) {
            if (matcher.group(1) != null) {
                // 时间参数
                parts.add(matcher.group(1));
            } else if (matcher.group(2) != null) {
                // 普通参数
                parts.add(matcher.group(2));
            }
        }
        
        return parts.toArray(new String[0]);
    }
    
    /**
     * 获取命令工厂实例。
     * 
     * @return 命令工厂实例
     */
    public CommandFactory getCommandFactory() {
        return commandFactory;
    }
    
    /**
     * 检查是否应该退出系统。
     * 
     * @return 如果应该退出返回 true，否则返回 false
     */
    public boolean shouldQuit() {
        return commandFactory.getQuitCommand().shouldQuit();
    }
    
    /**
     * 重置退出标志。
     */
    public void resetQuitFlag() {
        commandFactory.getQuitCommand().resetQuitFlag();
    }
}