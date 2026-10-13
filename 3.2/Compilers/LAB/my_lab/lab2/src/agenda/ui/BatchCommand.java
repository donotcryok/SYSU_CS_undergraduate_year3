package agenda.ui;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

/**
 * 批处理命令（Batch Command）。
 * 
 * <p>处理批处理命令，格式为：batch [fileName]
 * 从指定文件中读取命令并逐行执行。</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）
 * - 调用 CommandParser 解析和执行命令
 * - 捕获异常并格式化输出</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public class BatchCommand implements Command {
    
    /**
     * 构造函数，初始化批处理命令。
     */
    public BatchCommand() {
        // 无需初始化，CommandParser 在 execute 中创建
    }
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称 "batch"
     */
    @Override
    public String getName() {
        return "batch";
    }
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明
     */
    @Override
    public String getUsage() {
        return "batch [fileName] - 执行批处理文件中的命令";
    }
    
    /**
     * 执行批处理命令。
     * 
     * @param args 命令参数数组，args[0] 为文件名
     * @return 执行结果消息
     */
    @Override
    public String execute(String[] args) {
        // 检查参数数量
        if (args == null || args.length < 1) {
            return "错误: 参数不足\n用法: " + getUsage();
        }
        
        String fileName = args[0];
        StringBuilder result = new StringBuilder();
        int successCount = 0;
        int failCount = 0;
        
        // 创建新的 CommandParser 用于批处理
        CommandParser commandParser = new CommandParser();
        
        try (BufferedReader reader = new BufferedReader(new FileReader(fileName))) {
            String line;
            int lineNumber = 0;
            
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                line = line.trim();
                
                // 跳过空行和注释行
                if (line.isEmpty() || line.startsWith("#") || line.startsWith("//")) {
                    continue;
                }
                
                // 执行命令
                String output = commandParser.parseAndExecute(line);
                result.append("[").append(lineNumber).append("] ").append(line).append("\n");
                result.append("    ").append(output).append("\n");
                
                if (output.startsWith("错误")) {
                    failCount++;
                } else {
                    successCount++;
                }
                
                // 检查是否应该退出
                if (commandParser.shouldQuit()) {
                    break;
                }
            }
            
            result.append("\n批处理完成: 成功 ").append(successCount).append(" 个, 失败 ").append(failCount).append(" 个");
            
        } catch (IOException e) {
            return "错误: 无法读取文件 '" + fileName + "' - " + e.getMessage();
        }
        
        return result.toString();
    }
}