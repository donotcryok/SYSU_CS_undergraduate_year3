/**
 * 税率项类，用于表示超额累进税率表中的某一级。
 */
public class TaxRateItem {
    private double lowerBound; // 起点（不含）
    private double upperBound; // 终点（含）
    private double rate;       // 税率（如 0.05 表示 5%）

    /**
     * 构造函数
     * @param lowerBound 该级起点的金额
     * @param upperBound 该级终点的金额（若无上限可设为 Double.MAX_VALUE）
     * @param rate 该级对应的税率
     */
    public TaxRateItem(double lowerBound, double upperBound, double rate) {
        this.lowerBound = lowerBound;
        this.upperBound = upperBound;
        this.rate = rate;
    }

    /**
     * @return 获取该档次的纳税起点
     */
    public double getLowerBound() { return lowerBound; }
    /**
     * @return 获取该档次的纳税终点
     */
    public double getUpperBound() { return upperBound; }
    /**
     * @return 获取该档次的税率
     */
    public double getRate() { return rate; }
}