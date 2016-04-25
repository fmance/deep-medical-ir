package ch.ethz.inf.da.cds.ir.scorers;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.store.NIOFSDirectory;

import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

import com.google.common.base.Functions;
import com.google.common.collect.ImmutableSortedMap;
import com.google.common.collect.Ordering;

public abstract class Scorer {
    public static enum OutputType {
        TOP_1000_TREC_STYLE, ALL
    };

    protected final IndexReader reader;
    protected final Map<Integer, Integer> docIdMapping;

    public Scorer(Path indexDir) throws IOException {
        this.reader = DirectoryReader.open(NIOFSDirectory.open(indexDir));
        this.docIdMapping = LuceneUtils.getLuceneToPmcIdMapping(reader);
    }

    public void close() throws IOException {
        reader.close();
    }

    public void scoreQueries(String field, Path queries, Path output, OutputType resultType) throws Exception {
        long start = System.currentTimeMillis();
        List<TrecQuery> trecQueries = XmlUtils.parseQueries(queries.toFile());

        Map<Integer, Double> norms = getNorms(field);

        PrintWriter pw = new PrintWriter(output.toFile());
        for (TrecQuery trecQuery : trecQueries) {
            int queryId = trecQuery.getId();
            System.out.println("Scoring query " + queryId);
            Map<Integer, Double> scores = scoreQuery(trecQuery, field, norms);
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

    protected abstract Map<Integer, Double> getNorms(String field) throws IOException;

    protected abstract Map<Integer, Double> scoreQuery(TrecQuery trecQuery, String field,
            Map<Integer, Double> norms) throws Exception;

    private void writeTopScoresTrecStyle(Map<Integer, Double> scores, int queryId, PrintWriter pw) {
        Map<Integer, Double> sortedScores = sortMapByValuesDescending(scores);
        int rank = 1;
        for (Map.Entry<Integer, Double> entry : sortedScores.entrySet()) {
            int docId = entry.getKey();
            double score = entry.getValue();
            if (rank <= 1000) {
                pw.printf("%d Q0 %d %d %f STANDARD\n", queryId, docIdMapping.get(docId), rank, score);
            }
            rank++;
        }
    }

    private static <K extends Comparable<K>, V extends Comparable<V>> Map<K, V> sortMapByValuesDescending(
            Map<K, V> map) {
        final Ordering<K> reverseValuesAndNaturalKeysOrdering = Ordering.natural().reverse().nullsLast()
                .onResultOf(Functions.forMap(map, null)).compound(Ordering.natural());
        return ImmutableSortedMap.copyOf(map, reverseValuesAndNaturalKeysOrdering);
    }

    private void writeAllScores(Map<Integer, Double> scores, int queryId, PrintWriter pw) {
        for (Map.Entry<Integer, Double> entry : scores.entrySet()) {
            int docId = entry.getKey();
            double score = entry.getValue();
            pw.printf("%d %d %f STANDARD\n", queryId, docIdMapping.get(docId), score);
        }
    }
}
