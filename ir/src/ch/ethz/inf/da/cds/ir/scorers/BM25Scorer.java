package ch.ethz.inf.da.cds.ir.scorers;

import java.io.IOException;
import java.util.List;

import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.LeafReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.PostingsEnum;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.CollectionStatistics;

import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

public class BM25Scorer extends Scorer {
    private static final float k1 = 1.2f;
    private static final float b = 0.75f;

    public BM25Scorer(IndexReader reader) throws IOException {
        super(reader);
    }

    @Override
    protected float computeNorm(float docLength, float avgDocLength) {
        return k1 * (1 - b + b * docLength / avgDocLength);
    }

    @Override
    protected float[] scoreQuery(TrecQuery trecQuery, String field, float[] norms) throws Exception {
        CollectionStatistics stats = searcher.collectionStatistics(field);
        List<Term> queryTerms = LuceneUtils.getQueryTerms(reader, trecQuery, field);
        float[] scores = new float[reader.maxDoc()];

        for (Term queryTerm : queryTerms) {
            float weight = (k1 + 1) * idf(reader.docFreq(queryTerm), stats.docCount());
            for (LeafReaderContext ctx : reader.leaves()) {
                LeafReader leafReader = ctx.reader();
                PostingsEnum postingsEnum = leafReader.postings(queryTerm);
                if (postingsEnum == null) {
                    continue;
                }
                int docId;
                while ((docId = postingsEnum.nextDoc()) != PostingsEnum.NO_MORE_DOCS) {
                    int globalDocId = docId + ctx.docBase;
                    float tf = postingsEnum.freq();
                    scores[globalDocId] += weight * tf / (tf + norms[globalDocId]);
                }
            }
        }

        return scores;
    }

    private float idf(long docFreq, long docCount) throws IOException {
        return (float) Math.log(1 + (docCount - docFreq + 0.5) / (docFreq + 0.5));
    }
}
