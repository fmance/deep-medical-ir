package ch.ethz.inf.da.cds.ir;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.LeafReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.PostingsEnum;
import org.apache.lucene.index.Term;
import org.apache.lucene.store.NIOFSDirectory;

import ch.ethz.inf.da.cds.ir.util.DocUtils;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

import com.google.common.base.Functions;
import com.google.common.collect.ImmutableSortedMap;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;
import com.google.common.collect.Sets;

public class Stats {
    private static final double k1 = 1.2;
    private static final double b = 0.75;
    private static final List<Integer> docIds = DocUtils.getValidDocIds().stream().map(Integer::parseInt)
            .collect(Collectors.toList());

    private static Map<Integer, Double> stats(IndexReader reader, List<Term> queryTerms,
            Map<Integer, Double> norms, Map<Term, Double> idfs) throws IOException {
        Map<Integer, Double> scores = Maps.newHashMap();

        long start = System.currentTimeMillis();

        for (Term queryTerm : queryTerms) {
            double idf = idfs.get(queryTerm);
            for (LeafReaderContext ctx : reader.leaves()) {
                LeafReader leafReader = ctx.reader();
                PostingsEnum postingsEnum = leafReader.postings(queryTerm);
                if (postingsEnum != null) {
                    int docId;
                    while ((docId = postingsEnum.nextDoc()) != PostingsEnum.NO_MORE_DOCS) {
                        // int pmcid =
                        // LuceneUtils.getPmcId(leafReader.document(docId));
                        int globalId = docId + ctx.docBase;
                        int tf = postingsEnum.freq();
                        double score = scores.getOrDefault(globalId, 0.0);
                        double norm = norms.get(globalId);
                        score += idf * tf / (tf + norm);
                        scores.put(globalId, score);
                    }
                }

            }
        }

        // for (Term queryTerm : queryTerms) {
        // Map<Integer, Integer> queryTermFreq =
        // LuceneUtils.getTermFrequencies(reader, queryTerm);
        // double idf = idfs.get(queryTerm);
        // for (int docId : docIds) {
        // double score = scores.getOrDefault(docId, 0.0);
        // int tf = queryTermFreq.getOrDefault(docId, 0);
        // double norm = norms.get(docId);
        // score += idf * tf / (tf + norm);
        // scores.put(docId, score);
        // }
        // }

        // int count = 0;
        // for (int docId : docIds) {
        // double score = 0;
        // double norm = norms.get(docId);
        // for (Term queryTerm : queryTerms) {
        // int tf = termFreq.get(queryTerm).getOrDefault(docId, 0);
        // double idf = idfs.get(queryTerm);
        // score += idf * tf / (tf + norm);
        // }
        // scores.put(docId, score);
        // count++;
        // if (count % 1000 == 0) {
        // System.out.println(count);
        // }
        // }

        long end = System.currentTimeMillis();
        System.out.println("Time " + (end - start) / (1e3) + " sec");

        return scores;
    }

    private static Map<Term, Double> getBM25Idfs(IndexReader reader, Set<Term> terms) throws IOException {
        Map<Term, Double> bm25Idfs = Maps.newHashMap();
        for (Term term : terms) {
            int df = reader.docFreq(term);
            double idf = Math.log(1 + (docIds.size() - df + 0.5) / (df + 0.5));
            bm25Idfs.put(term, idf * (k1 + 1));
        }
        return bm25Idfs;
    }

    private static Map<Integer, Double> getBM25Norms(IndexReader reader, Map<Integer, Long> docLengths,
            double avgDocLen) throws IOException {
        Map<Integer, Double> bm25Norms = Maps.newHashMap();
        for (int docId = 0; docId < reader.numDocs(); docId++) {
            long docLen = docLengths.get(docId);
            double norm = k1 * (1 - b + b * docLen / avgDocLen);
            bm25Norms.put(docId, norm);
        }
        return bm25Norms;
    }

    public static <K extends Comparable<K>> Map<K, Double> sortMapByValuesDescending(Map<K, Double> map) {
        final Ordering<K> reverseValuesAndNaturalKeysOrdering = Ordering.natural().reverse().nullsLast()
                .onResultOf(Functions.forMap(map, null)).compound(Ordering.natural());
        return ImmutableSortedMap.copyOf(map, reverseValuesAndNaturalKeysOrdering);
    }

    public static void main(String[] args) throws Exception {
        DirectoryReader reader = DirectoryReader.open(NIOFSDirectory.open(FilePaths.INDEX_DIR));
        double avgDocLen = (double) reader.getSumTotalTermFreq("text") / reader.maxDoc();

        List<TrecQuery> trecQueries = XmlUtils.parseQueries(FilePaths.QUERIES_2014_FILE.toFile());
        PrintWriter pw = new PrintWriter("bm25-stats.txt");

        Map<Integer, Long> docLengths = LuceneUtils.getDocLengths(reader);
        Map<Integer, Double> bm25Norms = getBM25Norms(reader, docLengths, avgDocLen);

        long start = System.currentTimeMillis();

        for (TrecQuery trecQuery : trecQueries) {
            System.out.println("Query " + trecQuery.getId());
            List<Term> queryTerms = LuceneUtils.getQueryTerms(reader, trecQuery);
            Map<Integer, Double> bm25scores = stats(reader, queryTerms, bm25Norms,
                    getBM25Idfs(reader, Sets.newHashSet(queryTerms)));
            Map<Integer, Double> sortedScores = sortMapByValuesDescending(bm25scores);
            int rank = 1;
            for (Map.Entry<Integer, Double> entry : sortedScores.entrySet()) {
                int docId = entry.getKey();
                double score = entry.getValue();
                if (rank <= 1000) {
                    pw.printf("%d Q0 %d %d %f STANDARD\n", trecQuery.getId(),
                            LuceneUtils.getPmcId(reader.document(docId)), rank, score);
                }
                rank++;
            }
        }

        long end = System.currentTimeMillis();
        System.out.println("Time " + (end - start) / (1e3 * 60) + " minutes");

        reader.close();
        pw.close();
    }
}
