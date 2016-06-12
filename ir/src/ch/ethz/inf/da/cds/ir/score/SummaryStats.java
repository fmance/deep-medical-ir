package ch.ethz.inf.da.cds.ir.score;

import java.util.List;

import com.google.common.collect.Lists;

public class SummaryStats {
    private final double sum;
    private final double min;
    private final double max;
    private final double mean;

    public SummaryStats(double sum, double min, double max, double mean) {
        this.sum = sum;
        this.min = min;
        this.max = max;
        this.mean = mean;
    }

    public List<Double> toList() {
        return Lists.newArrayList(sum, min, max, mean);
    }

}
