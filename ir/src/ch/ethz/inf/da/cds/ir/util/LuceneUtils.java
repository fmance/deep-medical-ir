package ch.ethz.inf.da.cds.ir.util;

import java.io.IOException;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.analysis.tokenattributes.CharTermAttribute;
import org.apache.lucene.analysis.util.CharArraySet;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.LeafReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.NumericDocValues;
import org.apache.lucene.queryparser.classic.MultiFieldQueryParser;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.CollectionStatistics;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.similarities.BM25Similarity;
import org.apache.lucene.search.similarities.LMDirichletSimilarity;
import org.apache.lucene.search.similarities.Similarity;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.NIOFSDirectory;
import org.apache.lucene.util.SmallFloat;

import ch.ethz.inf.da.cds.ir.Article;
import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.SearchResult;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

//class MyAnalyzer extends StopwordAnalyzerBase {
//    @Override
//    protected TokenStreamComponents createComponents(String fieldName) {
//        final Tokenizer source = new StandardTokenizer();
//        TokenStream result = new StandardFilter(source);
//        result = new EnglishPossessiveFilter(result);
//        result = new LowerCaseFilter(result);
//        result = new StopFilter(result, stopwords);
//        result = new PorterStemFilter(result);
//        return new TokenStreamComponents(source, result);
//    }
//}

public class LuceneUtils {
    public static final String PMCID_FIELD = "pmcid";
    public static final String TITLE_FIELD = "title";
    public static final String TEXT_FIELD = "text";

    public static final CharArraySet stopWords = getIndriStopWords();

    public static CharArraySet getIndriStopWords() {
        CharArraySet stopWords = new CharArraySet(1000, true);
        try {
            for (String line : Files.readAllLines(FilePaths.DATA_DIR.resolve("indri-stopwords.txt"))) {
                line = line.trim();
                stopWords.add(line);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return stopWords;
    }

    public static IndexWriter getIndexWriter(Path indexPath, Similarity similarity) throws IOException {
        Directory directory = NIOFSDirectory.open(indexPath);
        IndexWriterConfig config = new IndexWriterConfig(new EnglishAnalyzer(stopWords));
        config.setRAMBufferSizeMB(4 * 1024);
        config.setSimilarity(similarity);
        return new IndexWriter(directory, config);
    }

    public static IndexWriter getBM25IndexWriter() throws IOException {
        return getIndexWriter(FilePaths.BM25_INDEX_DIR, new BM25Similarity());
    }

    public static IndexWriter getLMDirichletIndexWriter() throws IOException {
        return getIndexWriter(FilePaths.LM_DIRICHLET_INDEX_DIR, new LMDirichletSimilarity(7000));
    }

    // public static IndexWriter getTFIDFIndexWriter() throws IOException {
    // return getIndexWriter(FilePaths.TFIDF_INDEX_DIR, new
    // ClassicSimilarity());
    // }

    public static void index(IndexWriter indexWriter, Article article) throws IOException {
        Document doc = new Document();
        doc.add(new StringField(PMCID_FIELD, article.getPmcid(), Field.Store.YES));
        doc.add(new TextField(TITLE_FIELD, article.getTitle(), Field.Store.NO));
        doc.add(new TextField(TEXT_FIELD, article.getText(), Field.Store.NO));
        indexWriter.addDocument(doc);
    }

    private static List<SearchResult> searchIndex(Path indexPath,
                                                  Similarity similarity,
                                                  Query luceneQuery,
                                                  int numResults) throws IOException, ParseException {
        DirectoryReader ireader = DirectoryReader.open(NIOFSDirectory.open(indexPath));
        IndexSearcher isearcher = new IndexSearcher(ireader);
        isearcher.setSimilarity(similarity);

        ScoreDoc[] hits = isearcher.search(luceneQuery, numResults).scoreDocs;

        List<SearchResult> results = Lists.newArrayList();
        int rank = 1;
        for (ScoreDoc hit : hits) {
            Document doc = isearcher.doc(hit.doc);
            results.add(new SearchResult(doc.getField(PMCID_FIELD).stringValue(), rank++, hit.score));
        }
        ireader.close();

        return results;
    }

    public static List<SearchResult> searchBM25Index(Query luceneQuery, int numResults) throws IOException,
            ParseException {
        return searchIndex(FilePaths.BM25_INDEX_DIR, new BM25Similarity(), luceneQuery, numResults);
    }

    public static List<SearchResult> searchBM25Index(String queryString, String field, int numResults)
            throws IOException, ParseException {
        Query luceneQuery = constructLuceneQuery(queryString, field);
        return searchIndex(FilePaths.BM25_INDEX_DIR, new BM25Similarity(), luceneQuery, numResults);
    }

    public static List<SearchResult> searchLMDirichletIndex(String queryString, String field, int numResults)
            throws IOException, ParseException {
        Query luceneQuery = constructLuceneQuery(queryString, field);
        return searchIndex(FilePaths.LM_DIRICHLET_INDEX_DIR, new LMDirichletSimilarity(7000), luceneQuery, numResults);
    }

    // public static List<SearchResult> searchTFIDFIndex(TrecQuery trecQuery,
    // String field, int numResults)
    // throws IOException, ParseException {
    // return searchIndex(FilePaths.TFIDF_INDEX_DIR, new ClassicSimilarity(),
    // trecQuery, field, numResults);
    // }

    private static Query constructLuceneQuery(String queryString, String field) throws ParseException {
        Map<String, Float> boosts = Maps.newHashMap();
        boosts.put(TEXT_FIELD, 3f);
        boosts.put(TITLE_FIELD, 0f);

        QueryParser parser = new MultiFieldQueryParser(new String[] { TEXT_FIELD, TITLE_FIELD },
                                                       new EnglishAnalyzer(stopWords),
                                                       boosts);
        return parser.parse(QueryParser.escape(queryString));
        // if (trecQuery.getDiagnosis().isPresent()) {
        // Query diagnosisQuery = parser.parse(QueryParser.escape(trecQuery.getDiagnosis().get()));
        // BooleanQuery.Builder queryBuilder = new BooleanQuery.Builder();
        // queryBuilder.add(summaryQuery, BooleanClause.Occur.MUST);
        // queryBuilder.add(diagnosisQuery, BooleanClause.Occur.MUST);
        // return queryBuilder.build();
        // } else {
        // return summaryQuery;
        // }
    }

    public static int[] getLuceneToPmcIdMapping(IndexReader reader) throws IOException {
        int[] mapping = new int[reader.maxDoc()];
        for (int docId = 0; docId < reader.maxDoc(); docId++) {
            int pmcid = Integer.parseInt(reader.document(docId).getField(PMCID_FIELD).stringValue());
            mapping[docId] = pmcid;
        }
        return mapping;
    }

    public static float[] readFieldLengths(String field, IndexReader reader) throws IOException {
        float[] lengths = new float[reader.maxDoc()];

        for (LeafReaderContext ctx : reader.leaves()) {
            LeafReader leafReader = ctx.reader();
            NumericDocValues docValues = leafReader.getNormValues(field);
            for (int docId = 0; docId < leafReader.numDocs(); docId++) {
                lengths[docId + ctx.docBase] = decodeNormValue(docValues.get(docId));
            }
        }
        return lengths;
    }

    private static float decodeNormValue(long value) {
        float f = SmallFloat.byte315ToFloat((byte) value);
        return 1 / (f * f);
    }

    public static long getDocCount(String field, IndexReader reader) throws IOException {
        IndexSearcher searcher = new IndexSearcher(reader);
        CollectionStatistics stats = searcher.collectionStatistics(field);
        return stats.docCount();
    }

    public static float getAvgFieldLength(String field, IndexReader reader) throws IOException {
        IndexSearcher searcher = new IndexSearcher(reader);
        CollectionStatistics stats = searcher.collectionStatistics(field);
        return ((float) stats.sumTotalTermFreq()) / stats.docCount();
    }

    public static List<String> tokenizeString(Analyzer analyzer, String string) {
        List<String> result = new ArrayList<String>();
        try {
            TokenStream stream = analyzer.tokenStream(null, new StringReader(string));
            stream.reset();
            while (stream.incrementToken()) {
                result.add(stream.getAttribute(CharTermAttribute.class).toString());
            }
            stream.end();
            stream.close();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return result;
    }

    public static void main(String[] args) {
        Analyzer analyzer = new EnglishAnalyzer(getIndriStopWords());
        System.out.println(tokenizeString(analyzer, "hello there how are you doing, mate? I'm (16)!?, years old."));
    }
}
