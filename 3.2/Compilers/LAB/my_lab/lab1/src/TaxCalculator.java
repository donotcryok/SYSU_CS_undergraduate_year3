import java.util.ArrayList;
import java.util.List;

/**
 * 个人所得税计算器类。
 */
public class TaxCalculator {
    private double threshold; // 免征基数（起征点）
    private List<TaxRateItem> rateTable; // 税率表

    /**
     * 构造函数，初始化起征点并加载默认税率表
     * @param threshold 初始个人所得税起征点
     */
    public TaxCalculator(double threshold) {
        this.threshold = threshold;
        this.rateTable = new ArrayList<>();
        initializeDefaultRates();
    }

    /**
     * 初始化实验要求的默认 5 级税率
     */
    private void initializeDefaultRates() {
        rateTable.clear();
        rateTable.add(new TaxRateItem(0, 500, 0.05));
        rateTable.add(new TaxRateItem(500, 2000, 0.10));
        rateTable.add(new TaxRateItem(2000, 5000, 0.15));
        rateTable.add(new TaxRateItem(5000, 20000, 0.20));
        rateTable.add(new TaxRateItem(20000, Double.MAX_VALUE, 0.25));
    }

    /**
     * 修改起征点
     * @param threshold 新的起征点金额
     */
    public void setThreshold(double threshold) {
        if (threshold < 0) throw new IllegalArgumentException("起征点不能为负数");
        this.threshold = threshold;
    }

    /**
     * 核心算法：计算个人所得税
     * @param totalIncome 月工资薪金总额
     * @return 应缴纳税额
     */
    public double calculate(double totalIncome) {
        double taxableIncome = totalIncome - threshold; // 应纳税所得额
        if (taxableIncome <= 0) {
            return 0.0;
        }

        double totalTax = 0.0;
        for (TaxRateItem item : rateTable) {
            if (taxableIncome > item.getLowerBound()) {
                // 计算落在该档次内的金额
                double slice = Math.min(taxableIncome, item.getUpperBound()) - item.getLowerBound();
                totalTax += slice * item.getRate();
            }
        }
        return totalTax;
    }
    
    /**
     * 获取当前起征点
     * @return 起征点金额
     */
    public double getThreshold() { return threshold; }
}