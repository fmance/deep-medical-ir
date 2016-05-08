package ch.ethz.inf.da.cds.ir.scorers;


public class BM25Scorer {
    private static final float k1 = 1.2f;
    private static final float b = 0.75f;
    private static final float delta = 0f;

    // public BM25Scorer(IndexReader reader) throws IOException {
    // super(reader);
    // }
    //
    // public float[] scoreQuery(String field, TrecQuery trecQuery) throws
    // Exception {
    // float[] fieldLengths = LuceneUtils.readFieldLengths(field, reader);
    // long docCount = LuceneUtils.getDocCount(field, reader);
    // float avgFieldLength = LuceneUtils.getAvgFieldLength(field, reader);
    // List<Term> queryTerms = LuceneUtils.getQueryTerms(reader, trecQuery,
    // field);
    //
    // float[] scores = new float[reader.maxDoc()];
    //
    // for (Term queryTerm : queryTerms) {
    // float weight = (k1 + 1) * idf(reader.docFreq(queryTerm), docCount);
    // for (LeafReaderContext ctx : reader.leaves()) {
    // LeafReader leafReader = ctx.reader();
    // PostingsEnum postingsEnum = leafReader.postings(queryTerm);
    // if (postingsEnum == null) {
    // continue;
    // }
    // int docId;
    // while ((docId = postingsEnum.nextDoc()) != PostingsEnum.NO_MORE_DOCS) {
    // int globalDocId = docId + ctx.docBase;
    // float freq = postingsEnum.freq();
    // float normFreq = freq / norm(fieldLengths[globalDocId], avgFieldLength);
    // if (normFreq > 0) {
    // scores[globalDocId] += weight * (normFreq + delta) / (k1 + normFreq +
    // delta);
    // }
    // }
    // }
    // }
    //
    // return scores;
    // }
    //
    // private float idf(long docFreq, long docCount) throws IOException {
    // return (float) Math.log(1 + (docCount - docFreq + 0.5) / (docFreq +
    // 0.5));
    // }
    //
    // private float norm(float docLength, float avgDocLength) {
    // return (1 - b + b * docLength / avgDocLength);
    // }
}
