package ch.ethz.inf.da.cds.ir.scorers;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import org.apache.lucene.index.LeafReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.NumericDocValues;
import org.apache.lucene.index.PostingsEnum;
import org.apache.lucene.index.Term;

import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

import com.google.common.collect.Maps;

public class BM25Scorer extends Scorer {
    private static final double k1 = 1.2;
    private static final double b = 0.75;

    public BM25Scorer(Path indexDir) throws IOException {
        super(indexDir);
    }

    public static void main(String[] args) throws Exception {
        BM25Scorer scorer = new BM25Scorer(FilePaths.BM25_INDEX_DIR);
        scorer.scoreQueries(LuceneUtils.TEXT_FIELD, FilePaths.QUERIES_2014_FILE,
                FilePaths.BM25_SCORES_2014_FILE, OutputType.TOP_1000_TREC_STYLE);
        scorer.close();
    }

    @Override
    protected Map<Integer, Double> getNorms(String field) throws IOException {
        double avgDocLen = ((double) reader.getSumTotalTermFreq(field)) / reader.numDocs();
        Map<Integer, Double> norms = Maps.newHashMap();

        for (LeafReaderContext ctx : reader.leaves()) {
            LeafReader leafReader = ctx.reader();
            NumericDocValues docValues = leafReader.getNormValues(field);
            for (int docId = 0; docId < leafReader.numDocs(); docId++) {
                long length = docValues.get(docId);
                double norm = k1 * (1 - b + b * length / avgDocLen);
                norms.put(docId + ctx.docBase, norm);
            }
        }
        return norms;
    }

    @Override
    protected Map<Integer, Double> scoreQuery(TrecQuery trecQuery, String field, Map<Integer, Double> norms)
            throws Exception {
        List<Term> queryTerms = LuceneUtils.getQueryTerms(reader, trecQuery, field);
        Map<Integer, Double> scores = Maps.newHashMap();

        for (Term queryTerm : queryTerms) {
            double weight = getWeight(queryTerm);
            for (LeafReaderContext ctx : reader.leaves()) {
                LeafReader leafReader = ctx.reader();
                PostingsEnum postingsEnum = leafReader.postings(queryTerm);
                if (postingsEnum == null) {
                    continue;
                }
                int docId;
                while ((docId = postingsEnum.nextDoc()) != PostingsEnum.NO_MORE_DOCS) {
                    int globalDocId = docId + ctx.docBase;
                    double tf = postingsEnum.freq();
                    double score = scores.getOrDefault(globalDocId, 0.0);
                    double norm = norms.get(globalDocId);
                    score += weight * tf / (tf + norm);
                    scores.put(globalDocId, score);
                }
            }
        }

        return scores;
    }

    private double getWeight(Term term) throws IOException {
        int df = reader.docFreq(term);
        double idf = Math.log(1 + (reader.numDocs() - df + 0.5) / (df + 0.5));
        return idf * (k1 + 1);
    }
}
