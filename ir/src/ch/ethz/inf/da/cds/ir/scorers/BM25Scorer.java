package ch.ethz.inf.da.cds.ir.scorers;

import java.io.IOException;
import java.util.List;

import org.apache.lucene.index.LeafReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.NumericDocValues;
import org.apache.lucene.index.PostingsEnum;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.CollectionStatistics;
import org.apache.lucene.util.SmallFloat;

import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

public class BM25Scorer extends Scorer {
    private static final float k1 = 1.2f;
    private static final float b = 0.75f;

    public BM25Scorer() throws IOException {
        super(FilePaths.BM25_INDEX_DIR);
    }

    public static void main(String[] args) throws Exception {
        BM25Scorer scorer = new BM25Scorer();
        scorer.scoreQueries(LuceneUtils.TEXT_FIELD, FilePaths.QUERIES_2014_FILE,
                FilePaths.BM25_SCORES_2014_FILE, OutputType.ALL);
        scorer.close();
    }

    @Override
    protected float[] getNorms(String field) throws IOException {
        CollectionStatistics stats = searcher.collectionStatistics(field);
        float avgDocLen = ((float) stats.sumTotalTermFreq()) / stats.docCount();
        float[] norms = new float[reader.maxDoc()];

        for (LeafReaderContext ctx : reader.leaves()) {
            LeafReader leafReader = ctx.reader();
            NumericDocValues docValues = leafReader.getNormValues(field);
            for (int docId = 0; docId < leafReader.numDocs(); docId++) {
                float length = decodeNormValue(docValues.get(docId));
                float norm = k1 * (1 - b + b * length / avgDocLen);
                norms[docId + ctx.docBase] = norm;
            }
        }
        return norms;
    }

    private float decodeNormValue(long value) {
        float f = SmallFloat.byte315ToFloat((byte) value);
        return 1 / (f * f);
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
