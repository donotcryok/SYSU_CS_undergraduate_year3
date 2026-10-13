import java.util.Scanner;

/**
 * 命令行界面应用程序。
 */
public class TaxApp {
    private TaxCalculator calculator;
    private Scanner scanner;

    /** 默认构造函数 */
    public TaxApp() {
        this.calculator = new TaxCalculator(1600); // 默认 1600
        this.scanner = new Scanner(System.in);
    }

    /** 启动程序主循环菜单 */
    public void start() {
        while (true) {
            System.out.println("\n--- 个人所得税计算系统 ---");
            System.out.println("1. 计算个人所得税");
            System.out.println("2. 调整起征点 (当前: " + calculator.getThreshold() + ")");
            System.out.println("3. 退出");
            System.out.print("请选择操作: ");

            String choice = scanner.nextLine();
            try {
                switch (choice) {
                    case "1": handleCalculate(); break;
                    case "2": handleSettings(); break;
                    case "3": System.exit(0);
                    default: System.out.println("无效选择，请重新输入。");
                }
            } catch (Exception e) {
                System.out.println("错误: 输入数据格式不正确！");
            }
        }
    }

    private void handleCalculate() {
        System.out.print("请输入当月工资薪金总额: ");
        double income = Double.parseDouble(scanner.nextLine());
        double tax = calculator.calculate(income);
        System.out.printf("您应缴纳的个人所得税为: %.2f 元\n", tax);
    }

    private void handleSettings() {
        System.out.print("请输入新的起征点金额: ");
        double newThreshold = Double.parseDouble(scanner.nextLine());
        calculator.setThreshold(newThreshold);
        System.out.println("设置成功！");
    }

    /** 程序主入口 */
    public static void main(String[] args) {
        new TaxApp().start();
    }
}