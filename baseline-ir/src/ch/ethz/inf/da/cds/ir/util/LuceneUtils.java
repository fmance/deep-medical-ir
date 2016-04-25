package ch.ethz.inf.da.cds.ir.util;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import org.apache.lucene.analysis.en.EnglishAnalyzer;
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
import org.apache.lucene.index.PostingsEnum;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.BooleanClause;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.NIOFSDirectory;

import ch.ethz.inf.da.cds.ir.Article;
import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.SearchResult;
import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.BM25SimilarityDocLen.BM25Model;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

public class LuceneUtils {
    private static final String PMCID_FIELD = "pmcid";
    private static final String TITLE_FIELD = "title";
    private static final String TEXT_FIELD = "text";

    public static IndexWriter getIndexWriter(Path indexPath) throws IOException {
        Directory directory = NIOFSDirectory.open(indexPath);
        IndexWriterConfig config = new IndexWriterConfig(new EnglishAnalyzer());
        config.setRAMBufferSizeMB(4 * 1024);
        config.setSimilarity(new BM25SimilarityDocLen(BM25Model.CLASSIC));
        return new IndexWriter(directory, config);
    }

    public static void index(IndexWriter indexWriter, Article article) throws IOException {
        Document doc = new Document();
        doc.add(new StringField(PMCID_FIELD, article.getPmcid(), Field.Store.YES));
        doc.add(new TextField(TITLE_FIELD, article.getTitle(), Field.Store.NO));
        doc.add(new TextField(TEXT_FIELD, article.getText(), Field.Store.NO));
        indexWriter.addDocument(doc);
    }

    public static List<SearchResult> searchIndex(Path indexPath, TrecQuery trecQuery, int numResults)
            throws IOException, ParseException {
        DirectoryReader ireader = DirectoryReader.open(NIOFSDirectory.open(indexPath));
        IndexSearcher isearcher = new IndexSearcher(ireader);
        isearcher.setSimilarity(new BM25SimilarityDocLen(BM25Model.CLASSIC));

        Query luceneQuery = constructLuceneQuery(trecQuery);
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

    private static Query constructLuceneQuery(TrecQuery trecQuery) throws ParseException {
        QueryParser parser = new QueryParser(TEXT_FIELD, new EnglishAnalyzer());
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

    public static List<Term> getQueryTerms(IndexReader reader, TrecQuery trecQuery) throws ParseException,
            IOException {
        BooleanQuery luceneQuery = (BooleanQuery) constructLuceneQuery(trecQuery);
        luceneQuery.rewrite(reader);
        List<Term> queryTerms = Lists.newArrayList();
        for (BooleanClause clause : luceneQuery.clauses()) {
            Term term = ((TermQuery) clause.getQuery()).getTerm();
            queryTerms.add(term);
        }
        return queryTerms;
    }

    public static Map<Integer, Integer> getTermFrequencies(IndexReader reader, Term term) throws IOException {
        Map<Integer, Integer> termFrequencies = Maps.newHashMap();
        for (LeafReaderContext ctx : reader.leaves()) {
            LeafReader leafReader = ctx.reader();
            PostingsEnum postingsEnum = leafReader.postings(term);
            if (postingsEnum != null) {
                int docId;
                while ((docId = postingsEnum.nextDoc()) != PostingsEnum.NO_MORE_DOCS) {
                    int pmcid = getPmcId(leafReader.document(docId));
                    int freq = postingsEnum.freq();
                    termFrequencies.put(pmcid, freq);
                }
            }
        }
        return termFrequencies;
    }

    public static int getTermFrequency(IndexReader reader, int docId, Term term) throws IOException {
        for (LeafReaderContext ctx : reader.leaves()) {
            int indexDocId = docId - ctx.docBase;
            LeafReader leafReader = ctx.reader();
            PostingsEnum postingsEnum = leafReader.postings(term);
            if (postingsEnum.advance(indexDocId) == indexDocId) {
                return postingsEnum.freq();
            }
        }
        return 0;
    }

    public static int getPmcId(Document document) throws IOException {
        return Integer.parseInt(document.getField(PMCID_FIELD).stringValue());
    }

    public static Map<Integer, Long> getDocLengths(IndexReader reader) throws IOException {
        Map<Integer, Long> docLengths = Maps.newHashMap();
        for (LeafReaderContext ctx : reader.leaves()) {
            LeafReader leafReader = ctx.reader();
            NumericDocValues norms = leafReader.getNormValues(TEXT_FIELD);
            for (int docId = 0; docId < leafReader.numDocs(); docId++) {
                // int pmcId = getPmcId(leafReader.document(docId));
                long length = norms.get(docId);
                docLengths.put(docId + ctx.docBase, length);
            }
        }
        return docLengths;
    }

    public static void main(String[] args) throws Exception {
        DirectoryReader reader = DirectoryReader.open(NIOFSDirectory.open(FilePaths.INDEX_DIR));
        // System.out.println(getTermFrequency(reader, , new Term(TEXT_FIELD,
        // "pattern")));
    }
}
