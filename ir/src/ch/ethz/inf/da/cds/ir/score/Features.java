package ch.ethz.inf.da.cds.ir.score;

import java.util.List;

import com.google.common.collect.Lists;

public class Features {
    private double overlap;
    private double coord;
    private double length;
    private double idf;
    private SummaryStats tfStats;
    private SummaryStats normTfStats;
    private SummaryStats tfidfStats;
    private double bm25;
    private double tfidf;

    public double getOverlap() {
        return overlap;
    }

    public double getCoord() {
        return coord;
    }

    public double getLength() {
        return length;
    }

    public double getIdf() {
        return idf;
    }

    public SummaryStats getTfStats() {
        return tfStats;
    }

    public SummaryStats getNormTfStats() {
        return normTfStats;
    }

    public SummaryStats getTfidfStats() {
        return tfidfStats;
    }

    public double getBm25() {
        return bm25;
    }

    public double getTfidf() {
        return tfidf;
    }

    public List<Double> toList() {
        List<Double> features = Lists.newArrayList();
        features.add(bm25);
        // features.add(tfidf);
        // features.add(overlap);
        // features.add(coord);
        // features.add(length);
        // features.add(idf);
        // features.addAll(tfStats.toList());
        // features.addAll(normTfStats.toList());
        // features.addAll(tfidfStats.toList());
        return features;
    }

    public static class Builder {
        private double overlap;
        private double coord;
        private double length;
        private double idf;
        private SummaryStats tfStats;
        private SummaryStats normTfStats;
        private SummaryStats tfidfStats;
        private double bm25;
        private double tfidf;

        public Builder overlap(double overlap) {
            this.overlap = overlap;
            return this;
        }

        public Builder coord(double coord) {
            this.coord = coord;
            return this;
        }

        public Builder length(double length) {
            this.length = length;
            return this;
        }

        public Builder idf(double idf) {
            this.idf = idf;
            return this;
        }

        public Builder tfStats(SummaryStats tfStats) {
            this.tfStats = tfStats;
            return this;
        }

        public Builder normTfStats(SummaryStats normTfStats) {
            this.normTfStats = normTfStats;
            return this;
        }

        public Builder tfidfStats(SummaryStats tfidfStats) {
            this.tfidfStats = tfidfStats;
            return this;
        }

        public Builder bm25(double bm25) {
            this.bm25 = bm25;
            return this;
        }

        public Builder tfidf(double tfidf) {
            this.tfidf = tfidf;
            return this;
        }

        public Features build() {
            return new Features(this);
        }
    }

    private Features(Builder builder) {
        this.overlap = builder.overlap;
        this.coord = builder.coord;
        this.length = builder.length;
        this.idf = builder.idf;
        this.tfStats = builder.tfStats;
        this.normTfStats = builder.normTfStats;
        this.tfidfStats = builder.tfidfStats;
        this.bm25 = builder.bm25;
        this.tfidf = builder.tfidf;
    }

    public static Features zeros() {
        return new Builder().build();
    }
}
