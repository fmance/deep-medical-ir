package ch.ethz.inf.da.cds.ir.scorers;

import java.util.List;

import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.store.NIOFSDirectory;

import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.scorers.Scorer.OutputType;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

public class Scorers {
    public static void main(String[] args) throws Exception {
        IndexReader reader = DirectoryReader.open(NIOFSDirectory.open(FilePaths.BM25_INDEX_DIR));
        int[] docIdMapping = LuceneUtils.getLuceneToPmcIdMapping(reader);

        String field = LuceneUtils.TEXT_FIELD;
        List<TrecQuery> trecQueries = XmlUtils.parseQueries(FilePaths.QUERIES_2014_FILE.toFile());

        TFIDFScorer tfidfScorer = new TFIDFScorer(reader);
        BM25Scorer bm25Scorer = new BM25Scorer(reader);

        float[][] tfidfScores = tfidfScorer.scoreQueries(field, trecQueries);
        float[][] bm25Scores = bm25Scorer.scoreQueries(field, trecQueries);

        Scorer.writeScores(bm25Scores, FilePaths.BM25_SCORES_2014_FILE, OutputType.TOP_1000_TREC_STYLE,
                docIdMapping);

        reader.close();
    }
}
