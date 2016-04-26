package ch.ethz.inf.da.cds.ir.scorers;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.PriorityQueue;

import org.apache.commons.lang3.tuple.Pair;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.store.NIOFSDirectory;

import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

public abstract class Scorer {
    public static enum OutputType {
        TOP_1000_TREC_STYLE, ALL
    };

    protected final IndexReader reader;
    protected final IndexSearcher searcher;
    protected final int[] docIdMapping;

    public Scorer(Path indexDir) throws IOException {
        this.reader = DirectoryReader.open(NIOFSDirectory.open(indexDir));
        this.searcher = new IndexSearcher(reader);
        this.docIdMapping = LuceneUtils.getLuceneToPmcIdMapping(reader);
    }

    public void close() throws IOException {
        reader.close();
    }

    public void scoreQueries(String field, Path queries, Path output, OutputType resultType) throws Exception {
        long start = System.currentTimeMillis();
        List<TrecQuery> trecQueries = XmlUtils.parseQueries(queries.toFile());

        float[] norms = getNorms(field);

        PrintWriter pw = new PrintWriter(output.toFile());
        for (TrecQuery trecQuery : trecQueries) {
            int queryId = trecQuery.getId();
            System.out.println("Scoring query " + queryId);
            float[] scores = scoreQuery(trecQuery, field, norms);
            if (resultType == OutputType.TOP_1000_TREC_STYLE) {
                writeTopScoresTrecStyle(scores, queryId, pw);
            } else {
                writeAllScores(scores, queryId, pw);
            }
        }
        pw.close();

        long end = System.currentTimeMillis();
        System.out.println("Time " + (end - start) / (1e3 * 60) + " minutes");
    }

    protected abstract float[] getNorms(String field) throws IOException;

    protected abstract float[] scoreQuery(TrecQuery trecQuery, String field, float[] norms) throws Exception;

    private void writeTopScoresTrecStyle(float[] scores, int queryId, PrintWriter pw) {
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

    private PriorityQueue<Pair<Integer, Float>> getSortedScores(float[] scores) {
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

    private void writeAllScores(float[] scores, int queryId, PrintWriter pw) {
        for (int docId = 0; docId < scores.length; docId++) {
            pw.printf("%d %d %f\n", queryId, docIdMapping[docId], scores[docId]);
        }
    }
}
