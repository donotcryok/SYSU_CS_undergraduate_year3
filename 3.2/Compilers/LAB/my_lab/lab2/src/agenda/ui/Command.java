package agenda.ui;

/**
 * 命令接口（命令模式）。
 * 
 * <p>该接口定义了所有 CLI 命令的统一执行方法。
 * 采用命令模式（Command Pattern），将每个命令封装为独立的对象，
 * 使命令的调用者与执行者解耦，便于扩展新命令。</p>
 * 
 * <p>设计模式：命令模式（Command Pattern）
 * - 将命令请求封装为对象
 * - 支持命令的参数化和队列化
 * - 便于添加新命令，符合开闭原则</p>
 * 
 * <p>架构位置：表示层（Presentation Tier）
 * - 位于三层架构的最上层
 * - 调用业务逻辑层（Service）
 * - 负责捕获异常并格式化输出</p>
 * 
 * @author 马福泉
 * @version 1.0
 * @since 2026-03-01
 */
public interface Command {
    
    /**
     * 执行命令。
     * 
     * @param args 命令参数数组
     * @return 执行结果消息
     */
    String execute(String[] args);
    
    /**
     * 获取命令名称。
     * 
     * @return 命令名称
     */
    String getName();
    
    /**
     * 获取命令用法说明。
     * 
     * @return 命令用法说明字符串
     */
    String getUsage();
}