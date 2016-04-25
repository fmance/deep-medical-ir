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
import org.apache.lucene.search.similarities.ClassicSimilarity;

import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

import com.google.common.collect.Maps;

public class TFIDFScorer extends Scorer {
    public TFIDFScorer(Path indexDir) throws IOException {
        super(indexDir);
    }

    public static void main(String[] args) throws Exception {
        TFIDFScorer scorer = new TFIDFScorer(FilePaths.TFIDF_INDEX_DIR);
        scorer.scoreQueries(LuceneUtils.TEXT_FIELD, FilePaths.QUERIES_2015_A_FILE,
                FilePaths.TFIDF_SCORES_2015_FILE, OutputType.TOP_1000_TREC_STYLE);
        scorer.close();
    }

    @Override
    protected Map<Integer, Double> getNorms(String field) throws IOException {
        ClassicSimilarity similarity = new ClassicSimilarity();
        Map<Integer, Double> norms = Maps.newHashMap();
        for (LeafReaderContext ctx : reader.leaves()) {
            LeafReader leafReader = ctx.reader();
            NumericDocValues docValues = leafReader.getNormValues(field);
            for (int docId = 0; docId < leafReader.numDocs(); docId++) {
                norms.put(docId + ctx.docBase, (double) similarity.decodeNormValue(docValues.get(docId)));
            }
        }
        return norms;
    }

    @Override
    protected Map<Integer, Double> scoreQuery(TrecQuery trecQuery, String field, Map<Integer, Double> norms)
            throws Exception {
        List<Term> queryTerms = LuceneUtils.getQueryTerms(reader, trecQuery, field);
        Map<Term, Double> squaredWeights = getSquaredWeights(queryTerms);
        Map<Integer, Integer> overlaps = Maps.newHashMap();
        Map<Integer, Double> scores = Maps.newHashMap();

        for (Term queryTerm : queryTerms) {
            double squaredWeight = squaredWeights.get(queryTerm);
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
                    score += Math.sqrt(tf) * squaredWeight;
                    if (tf > 0) {
                        int overlap = overlaps.getOrDefault(globalDocId, 0);
                        overlaps.put(globalDocId, overlap + 1);
                    }
                    scores.put(globalDocId, score);
                }
            }
        }

        double queryNorm = 1 / (Math.sqrt(squaredWeights.values().stream().reduce(0.0, Double::sum)));

        for (Map.Entry<Integer, Double> docScore : scores.entrySet()) {
            int docId = docScore.getKey();
            double score = docScore.getValue();
            double coord = ((double) overlaps.get(docId)) / queryTerms.size();
            scores.put(docId, coord * queryNorm * score * norms.get(docId));
        }

        return scores;
    }

    private Map<Term, Double> getSquaredWeights(List<Term> terms) throws IOException {
        Map<Term, Double> squaredWeights = Maps.newHashMap();
        for (Term term : terms) {
            double idf = Math.log(reader.numDocs() / (double) (reader.docFreq(term) + 1)) + 1.0;
            squaredWeights.put(term, idf * idf);
        }
        return squaredWeights;
    }
}
