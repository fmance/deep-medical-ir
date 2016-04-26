package ch.ethz.inf.da.cds.ir.scorers;

import java.io.IOException;
import java.util.List;
import java.util.Map;

import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.LeafReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.PostingsEnum;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.CollectionStatistics;
import org.apache.lucene.search.similarities.ClassicSimilarity;

import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

import com.google.common.collect.Maps;

public class TFIDFScorer extends Scorer {
    private static final ClassicSimilarity SIMILARITY = new ClassicSimilarity();

    public TFIDFScorer(IndexReader reader) throws IOException {
        super(reader);
    }

    @Override
    protected float computeNorm(float docLength, float avgDocLength) {
        return (float) (1 / Math.sqrt(docLength));
    }

    @Override
    protected float[] scoreQuery(TrecQuery trecQuery, String field, float[] norms) throws Exception {
        List<Term> queryTerms = LuceneUtils.getQueryTerms(reader, trecQuery, field);
        CollectionStatistics stats = searcher.collectionStatistics(field);
        Map<Term, Float> squaredWeights = getSquaredWeights(queryTerms, stats.docCount());
        int[] overlaps = new int[reader.maxDoc()];
        float[] scores = new float[reader.maxDoc()];

        for (Term queryTerm : queryTerms) {
            float squaredWeight = squaredWeights.get(queryTerm);
            for (LeafReaderContext ctx : reader.leaves()) {
                LeafReader leafReader = ctx.reader();
                PostingsEnum postingsEnum = leafReader.postings(queryTerm);
                if (postingsEnum == null) {
                    continue;
                }
                int docId;
                while ((docId = postingsEnum.nextDoc()) != PostingsEnum.NO_MORE_DOCS) {
                    int globalDocId = docId + ctx.docBase;
                    float freq = postingsEnum.freq();
                    scores[globalDocId] += SIMILARITY.tf(freq) * squaredWeight;
                    overlaps[globalDocId] += (freq > 0) ? 1 : 0;
                }
            }
        }

        Float sumOfSquaredWeights = squaredWeights.values().stream().reduce(0.0f, Float::sum);
        float queryNorm = SIMILARITY.queryNorm(sumOfSquaredWeights);

        for (int docId = 0; docId < scores.length; docId++) {
            float score = scores[docId];
            float coord = SIMILARITY.coord(overlaps[docId], queryTerms.size());
            scores[docId] = coord * queryNorm * score * norms[docId];
        }

        return scores;
    }

    private Map<Term, Float> getSquaredWeights(List<Term> terms, long docCount) throws IOException {
        Map<Term, Float> squaredWeights = Maps.newHashMap();
        for (Term term : terms) {
            float idf = SIMILARITY.idf(reader.docFreq(term), docCount);
            squaredWeights.put(term, idf * idf);
        }
        return squaredWeights;
    }
}
