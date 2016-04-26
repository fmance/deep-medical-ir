package ch.ethz.inf.da.cds.ir.scorers;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.PriorityQueue;

import org.apache.commons.lang3.tuple.Pair;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.LeafReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.NumericDocValues;
import org.apache.lucene.search.CollectionStatistics;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.util.SmallFloat;

import ch.ethz.inf.da.cds.ir.TrecQuery;

public abstract class Scorer {
    public static enum OutputType {
        TOP_1000_TREC_STYLE, ALL
    };

    protected final IndexReader reader;
    protected final IndexSearcher searcher;

    public Scorer(IndexReader reader) throws IOException {
        this.reader = reader;
        this.searcher = new IndexSearcher(reader);
    }

    public float[][] scoreQueries(String field, List<TrecQuery> trecQueries) throws Exception {
        float[] norms = computeNorms(field);
        float[][] scores = new float[trecQueries.size()][reader.maxDoc()];

        for (TrecQuery trecQuery : trecQueries) {
            int queryId = trecQuery.getId();
            System.out.println("Scoring query " + queryId);
            scores[queryId - 1] = scoreQuery(trecQuery, field, norms);
        }

        return scores;
    }

    private float[] computeNorms(String field) throws IOException {
        CollectionStatistics stats = searcher.collectionStatistics(field);
        float avgDocLen = ((float) stats.sumTotalTermFreq()) / stats.docCount();
        float[] norms = new float[reader.maxDoc()];

        for (LeafReaderContext ctx : reader.leaves()) {
            LeafReader leafReader = ctx.reader();
            NumericDocValues docValues = leafReader.getNormValues(field);
            for (int docId = 0; docId < leafReader.numDocs(); docId++) {
                float length = decodeNormValue(docValues.get(docId));
                norms[docId + ctx.docBase] = computeNorm(length, avgDocLen);
            }
        }
        return norms;
    }

    protected float decodeNormValue(long value) {
        float f = SmallFloat.byte315ToFloat((byte) value);
        return 1 / (f * f);
    }

    protected abstract float computeNorm(float docLength, float avgDocLength);

    protected abstract float[] scoreQuery(TrecQuery trecQuery, String field, float[] norms) throws Exception;

    public static void writeScores(float[][] scores, Path output, OutputType resultType, int[] docIdMapping)
            throws Exception {
        PrintWriter pw = new PrintWriter(output.toFile());
        for (int queryId = 1; queryId <= scores.length; queryId++) {
            if (resultType == OutputType.TOP_1000_TREC_STYLE) {
                writeTopScoresTrecStyle(scores[queryId - 1], queryId, pw, docIdMapping);
            } else {
                writeAllScores(scores[queryId - 1], queryId, pw, docIdMapping);
            }
        }
        pw.close();
    }

    private static void writeTopScoresTrecStyle(float[] scores, int queryId, PrintWriter pw,
            int[] docIdMapping) {
        PriorityQueue<Pair<Integer, Float>> sortedScores = getSortedScores(scores);

        int rank = 1;
        for (int i = 0; i < 1000; i++) {
            Pair<Integer, Float> docScore = sortedScores.poll();
            int docId = docScore.getLeft();
            float score = docScore.getRight();
            if (rank <= 1000) {
                pw.printf("%d Q0 %d %d %f STANDARD\n", queryId, docIdMapping[docId], rank, score);
            }
            rank++;
        }
    }

    private static PriorityQueue<Pair<Integer, Float>> getSortedScores(float[] scores) {
        PriorityQueue<Pair<Integer, Float>> sortedScores = new PriorityQueue<>(
                Collections.reverseOrder(new Comparator<Pair<Integer, Float>>() {
                    @Override
                    public int compare(Pair<Integer, Float> o1, Pair<Integer, Float> o2) {
                        return o1.getRight().compareTo(o2.getRight());
                    }
                }));
        for (int docId = 0; docId < scores.length; docId++) {
            sortedScores.offer(Pair.of(docId, scores[docId]));
        }
        return sortedScores;
    }

    private static void writeAllScores(float[] scores, int queryId, PrintWriter pw, int[] docIdMapping) {
        for (int docId = 0; docId < scores.length; docId++) {
            pw.printf("%d %d %f\n", queryId, docIdMapping[docId], scores[docId]);
        }
    }
}
