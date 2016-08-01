package ch.ethz.inf.da.cds.ir.score;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

import org.apache.commons.lang3.tuple.Pair;
import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.LeafReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.PostingsEnum;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.BooleanClause;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.search.similarities.ClassicSimilarity;

import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

public class Scorer {
    public static enum Measure {
        BM25, TFIDF
    };

    private static final ClassicSimilarity SIMILARITY = new ClassicSimilarity();

    private static final float k1 = 1.2f;
    private static final float b = 0.75f;
    private static final float delta = 0.0f;

    private static double getQueryNorm(List<Term> terms, long docCount, IndexReader reader) throws IOException {
        double sumOfSquaredWeights = 0;
        for (Term term : terms) {
            float idf = SIMILARITY.idf(reader.docFreq(term), docCount);
            sumOfSquaredWeights += idf * idf;
        }
        return SIMILARITY.queryNorm((float) sumOfSquaredWeights);
    }

    public static Features[] getFeatures(String field, TrecQuery trecQuery, IndexReader reader) throws Exception {
        List<Term> queryTerms = getQueryTerms(reader, trecQuery, field);
        System.out.println(queryTerms);

        // double[] tfidfs = new double[reader.maxDoc()];
        double[] bm25s = new double[reader.maxDoc()];
        // double[] sumIdfs = new double[reader.maxDoc()];
        // int[] overlaps = new int[reader.maxDoc()];

        // double[] sumTfs = new double[reader.maxDoc()];
        // double[] minTf = new double[reader.maxDoc()];
        // Arrays.fill(minTf, Double.MAX_VALUE);
        // double[] maxTf = new double[reader.maxDoc()];

        // double[] sumTfIdfs = new double[reader.maxDoc()];
        // double[] minTfIdf = new double[reader.maxDoc()];
        // Arrays.fill(minTfIdf, Double.MAX_VALUE);
        // double[] maxTfIdf = new double[reader.maxDoc()];

        float[] fieldLengths = LuceneUtils.readFieldLengths(field, reader);
        float avgFieldLength = LuceneUtils.getAvgFieldLength(field, reader);

        long docCount = LuceneUtils.getDocCount(field, reader);
        // double queryNorm = getQueryNorm(queryTerms, docCount, reader);

        Features[] features = new Features[reader.maxDoc()];
        for (int i = 0; i < features.length; i++) {
            features[i] = Features.zeros();
        }

        for (Term queryTerm : queryTerms) {
            int docFreq = reader.docFreq(queryTerm);
            double bm25Weight = (k1 + 1) * Math.log(1 + (docCount - docFreq + 0.5) / (docFreq + 0.5));
            // double idf = SIMILARITY.idf(docFreq, docCount);

            for (LeafReaderContext ctx : reader.leaves()) {
                LeafReader leafReader = ctx.reader();
                PostingsEnum postingsEnum = leafReader.postings(queryTerm);
                if (postingsEnum == null) {
                    continue;
                }
                int docId;
                while ((docId = postingsEnum.nextDoc()) != PostingsEnum.NO_MORE_DOCS) {
                    int globalDocId = docId + ctx.docBase;
                    float fieldLength = fieldLengths[globalDocId];
                    int termFreq = postingsEnum.freq();

                    // float simTf = SIMILARITY.tf(termFreq);
                    // sumTfs[globalDocId] += simTf;
                    // minTf[globalDocId] = Math.min(simTf, minTf[globalDocId]);
                    // maxTf[globalDocId] = Math.max(simTf, maxTf[globalDocId]);

                    // double tfidf = simTf * idf * idf;
                    // sumTfIdfs[globalDocId] += tfidf;
                    // minTfIdf[globalDocId] = Math.min(tfidf,
                    // minTfIdf[globalDocId]);
                    // maxTfIdf[globalDocId] = Math.max(tfidf,
                    // maxTfIdf[globalDocId]);

                    // overlaps[globalDocId]++;
                    // sumIdfs[globalDocId] += idf;
                    //
                    // tfidfs[globalDocId] += tfidf;

                    double normFreq = termFreq / (1 - b + b * fieldLength / avgFieldLength);
                    bm25s[globalDocId] += bm25Weight * (normFreq + delta) / (k1 + normFreq + delta);
                }
            }
        }
        double bm25Max = Arrays.stream(bm25s).max().getAsDouble();
        for (int docId = 0; docId < reader.maxDoc(); docId++) {
            // double coord = (double) overlaps[docId] / queryTerms.size();
            // float fieldLength = fieldLengths[docId];
            // tfidfs[docId] *= (coord * queryNorm / Math.sqrt(fieldLength));

            SummaryStats tfStats = null;
            // new SummaryStats(sumTfs[docId], minTf[docId], maxTf[docId],
            // sumTfs[docId] / overlaps[docId]);
            SummaryStats normTfStats = null;
            // new SummaryStats(sumTfs[docId] / fieldLength,
            // minTf[docId] / fieldLength,
            // maxTf[docId] / fieldLength,
            // sumTfs[docId] / (overlaps[docId] * fieldLength));
            SummaryStats tfIdfStats = null;
            // new SummaryStats(sumTfIdfs[docId], minTfIdf[docId],
            // maxTfIdf[docId], sumTfIdfs[docId] / overlaps[docId]);

            features[docId] = new Features.Builder()
            // .overlap(overlaps[docId])
            // .coord(coord)
            // .length(fieldLength)
            // .idf(sumIdfs[docId])
            // .tfStats(tfStats)
            // .normTfStats(normTfStats)
            // .tfidfStats(tfIdfStats)
            // .tfidf(tfidfs[docId])
            .bm25(bm25s[docId] / bm25Max)
                                                    .build();

        }

        return features;
    }

    public static Map<Integer, Integer> getTopDocs(Features[] scores, int num, Measure measure) {
        PriorityQueue<Pair<Integer, Double>> sortedScores = getSortedScores(scores, measure);

        Map<Integer, Integer> rankings = Maps.newHashMap();
        int rank = 1;
        for (int i = 0; i < num; i++) {
            Pair<Integer, Double> docScore = sortedScores.poll();
            int docId = docScore.getLeft();
            rankings.put(docId, rank++);
        }
        return rankings;
    }

    public static void writeTopScores(Features[] scores,
                                      int queryId,
                                      int num,
                                      PrintWriter pw,
                                      int[] docIdMapping,
                                      Measure measure) throws Exception {
        PriorityQueue<Pair<Integer, Double>> sortedScores = getSortedScores(scores, measure);
        int rank = 1;
        for (int i = 0; i < num; i++) {
            Pair<Integer, Double> docScore = sortedScores.poll();
            int docId = docScore.getLeft();
            double score = docScore.getRight();
            pw.printf("%d Q0 %d %d %f STANDARD\n", queryId, docIdMapping[docId], rank, score);
            rank++;
        }
    }

    private static PriorityQueue<Pair<Integer, Double>> getSortedScores(Features[] scores, Measure measure) {
        PriorityQueue<Pair<Integer, Double>> sortedScores = new PriorityQueue<>(Collections.reverseOrder(new Comparator<Pair<Integer, Double>>() {
            @Override
            public int compare(Pair<Integer, Double> o1, Pair<Integer, Double> o2) {
                return o1.getRight().compareTo(o2.getRight());
            }
        }));
        for (int docId = 0; docId < scores.length; docId++) {
            if (measure == Measure.BM25) {
                sortedScores.offer(Pair.of(docId, scores[docId].getBm25()));
            } else if (measure == Measure.TFIDF) {
                sortedScores.offer(Pair.of(docId, scores[docId].getTfidf()));
            }
        }
        return sortedScores;
    }

    public static void writeTopScores(double[] scores, int queryId, int num, PrintWriter pw, int[] docIdMapping) {
        PriorityQueue<Pair<Integer, Double>> sortedScores = getSortedScores(scores);
        int rank = 1;
        for (int i = 0; i < num; i++) {
            Pair<Integer, Double> docScore = sortedScores.poll();
            int docId = docScore.getLeft();
            double score = docScore.getRight();
            pw.printf("%d Q0 %d %d %f STANDARD\n", queryId, docIdMapping[docId], rank, score);
            rank++;
        }
    }

    private static PriorityQueue<Pair<Integer, Double>> getSortedScores(double[] scores) {
        PriorityQueue<Pair<Integer, Double>> sortedScores = new PriorityQueue<>(Collections.reverseOrder(new Comparator<Pair<Integer, Double>>() {
            @Override
            public int compare(Pair<Integer, Double> o1, Pair<Integer, Double> o2) {
                return o1.getRight().compareTo(o2.getRight());
            }
        }));
        for (int docId = 0; docId < scores.length; docId++) {
            sortedScores.offer(Pair.of(docId, scores[docId]));
        }
        return sortedScores;
    }

    private static Query constructLuceneQuery(TrecQuery trecQuery, String field) throws ParseException {
        QueryParser parser = new QueryParser(field, new EnglishAnalyzer(LuceneUtils.getIndriStopWords()));
        Query summaryQuery = parser.parse(QueryParser.escape(trecQuery.getSummary()));
        if (trecQuery.getDiagnosis().isPresent()) {
            Query diagnosisQuery = parser.parse(QueryParser.escape(trecQuery.getDiagnosis().get()));
            BooleanQuery.Builder queryBuilder = new BooleanQuery.Builder();
            queryBuilder.add(summaryQuery, BooleanClause.Occur.MUST);
            queryBuilder.add(diagnosisQuery, BooleanClause.Occur.MUST);
            return queryBuilder.build();
        } else {
            return summaryQuery;
        }
    }

    public static List<Term> getQueryTerms(IndexReader reader, TrecQuery trecQuery, String field)
            throws ParseException, IOException {
        BooleanQuery luceneQuery = (BooleanQuery) constructLuceneQuery(trecQuery, field);
        luceneQuery.rewrite(reader);
        List<Term> queryTerms = Lists.newArrayList();
        for (BooleanClause clause : luceneQuery.clauses()) {
            Query clauseQuery = clause.getQuery();
            if (clauseQuery instanceof BooleanQuery) {
                for (BooleanClause subClause : ((BooleanQuery) clauseQuery).clauses()) {
                    System.out.println(subClause.getQuery());
                    queryTerms.add(((TermQuery) subClause.getQuery()).getTerm());
                }
            } else {
                Term term = ((TermQuery) clauseQuery).getTerm();
                queryTerms.add(term);
            }
        }
        return queryTerms;
    }

}
