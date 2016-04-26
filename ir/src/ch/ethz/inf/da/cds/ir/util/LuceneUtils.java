package ch.ethz.inf.da.cds.ir.util;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;

import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.BooleanClause;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.search.similarities.BM25Similarity;
import org.apache.lucene.search.similarities.ClassicSimilarity;
import org.apache.lucene.search.similarities.Similarity;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.NIOFSDirectory;

import ch.ethz.inf.da.cds.ir.Article;
import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.SearchResult;
import ch.ethz.inf.da.cds.ir.TrecQuery;

import com.google.common.collect.Lists;

public class LuceneUtils {
    public static final String PMCID_FIELD = "pmcid";
    public static final String TITLE_FIELD = "title";
    public static final String TEXT_FIELD = "text";

    public static IndexWriter getIndexWriter(Path indexPath, Similarity similarity) throws IOException {
        Directory directory = NIOFSDirectory.open(indexPath);
        IndexWriterConfig config = new IndexWriterConfig(new EnglishAnalyzer());
        config.setRAMBufferSizeMB(4 * 1024);
        config.setSimilarity(similarity);
        return new IndexWriter(directory, config);
    }

    public static IndexWriter getBM25IndexWriter() throws IOException {
        return getIndexWriter(FilePaths.BM25_INDEX_DIR, new BM25Similarity());
    }

    public static IndexWriter getTFIDFIndexWriter() throws IOException {
        return getIndexWriter(FilePaths.TFIDF_INDEX_DIR, new ClassicSimilarity());
    }

    public static void index(IndexWriter indexWriter, Article article) throws IOException {
        Document doc = new Document();
        doc.add(new StringField(PMCID_FIELD, article.getPmcid(), Field.Store.YES));
        doc.add(new TextField(TITLE_FIELD, article.getTitle(), Field.Store.NO));
        doc.add(new TextField(TEXT_FIELD, article.getText(), Field.Store.NO));
        indexWriter.addDocument(doc);
    }

    public static List<SearchResult> searchIndex(Path indexPath, Similarity similarity, TrecQuery trecQuery,
            String field, int numResults) throws IOException, ParseException {
        DirectoryReader ireader = DirectoryReader.open(NIOFSDirectory.open(indexPath));
        IndexSearcher isearcher = new IndexSearcher(ireader);
        isearcher.setSimilarity(similarity);

        Query luceneQuery = constructLuceneQuery(trecQuery, field);
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

    public static List<SearchResult> searchBM25Index(TrecQuery trecQuery, String field, int numResults)
            throws IOException, ParseException {
        return searchIndex(FilePaths.BM25_INDEX_DIR, new BM25Similarity(), trecQuery, field, numResults);
    }

    public static List<SearchResult> searchTFIDFIndex(TrecQuery trecQuery, String field, int numResults)
            throws IOException, ParseException {
        return searchIndex(FilePaths.TFIDF_INDEX_DIR, new ClassicSimilarity(), trecQuery, field, numResults);
    }

    private static Query constructLuceneQuery(TrecQuery trecQuery, String field) throws ParseException {
        QueryParser parser = new QueryParser(field, new EnglishAnalyzer());
        Query summaryQuery = parser.parse(QueryParser.escape(trecQuery.getSummary()));
        if (trecQuery.getDiagnosis().isPresent()) {
            Query diagnosisQuery = parser.parse(QueryParser.escape(trecQuery.getDiagnosis().get()));
            BooleanQuery.Builder queryBuilder = new BooleanQuery.Builder();
            queryBuilder.add(summaryQuery, BooleanClause.Occur.MUST);
            queryBuilder.add(diagnosisQuery, BooleanClause.Occur.MUST);
            return queryBuilder.build();
        } else {
            return summaryQuery;
        }
    }

    public static List<Term> getQueryTerms(IndexReader reader, TrecQuery trecQuery, String field)
            throws ParseException, IOException {
        BooleanQuery luceneQuery = (BooleanQuery) constructLuceneQuery(trecQuery, field);
        luceneQuery.rewrite(reader);
        List<Term> queryTerms = Lists.newArrayList();
        for (BooleanClause clause : luceneQuery.clauses()) {
            Term term = ((TermQuery) clause.getQuery()).getTerm();
            queryTerms.add(term);
        }
        return queryTerms;
    }

    public static int[] getLuceneToPmcIdMapping(IndexReader reader) throws IOException {
        int[] mapping = new int[reader.maxDoc()];
        for (int docId = 0; docId < reader.maxDoc(); docId++) {
            int pmcid = Integer.parseInt(reader.document(docId).getField(PMCID_FIELD).stringValue());
            mapping[docId] = pmcid;
        }
        return mapping;
    }
}
