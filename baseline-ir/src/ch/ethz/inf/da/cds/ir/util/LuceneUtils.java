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
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.BooleanClause;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.similarities.BM25Similarity;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.NIOFSDirectory;

import com.google.common.collect.Lists;

import ch.ethz.inf.da.cds.ir.Article;
import ch.ethz.inf.da.cds.ir.SearchResult;
import ch.ethz.inf.da.cds.ir.Topic;

public class LuceneUtils {
	private static final int MAX_SEARCH_RESULTS = 1000;
	private static final String PMCID_FIELD = "pmcid";
	private static final String TITLE_FIELD = "title";
	private static final String TEXT_FIELD = "text";

	public static IndexWriter getIndexWriter(Path indexPath) throws IOException {
		Directory directory = NIOFSDirectory.open(indexPath);
		IndexWriterConfig config = new IndexWriterConfig(new EnglishAnalyzer());
		config.setRAMBufferSizeMB(4 * 1024);
		config.setSimilarity(new BM25Similarity());
		return new IndexWriter(directory, config);
	}

	public static void index(IndexWriter indexWriter, Article article) throws IOException {
		Document doc = new Document();
		doc.add(new StringField(PMCID_FIELD, article.getPmcid(), Field.Store.YES));
		doc.add(new TextField(TITLE_FIELD, article.getTitle(), Field.Store.NO));
		doc.add(new TextField(TEXT_FIELD, article.getText(), Field.Store.NO));
		indexWriter.addDocument(doc);
	}

	public static List<SearchResult> searchIndex(Path indexPath, Topic topic) throws IOException, ParseException {
		DirectoryReader ireader = DirectoryReader.open(NIOFSDirectory.open(indexPath));
		IndexSearcher isearcher = new IndexSearcher(ireader);
		isearcher.setSimilarity(new BM25Similarity());

		Query luceneQuery = constructLuceneQuery(topic);
		ScoreDoc[] hits = isearcher.search(luceneQuery, MAX_SEARCH_RESULTS).scoreDocs;

		List<SearchResult> results = Lists.newArrayList();
		int rank = 1;
		for (ScoreDoc hit : hits) {
			Document doc = isearcher.doc(hit.doc);
			results.add(new SearchResult(doc.getField(PMCID_FIELD).stringValue(), rank++, hit.score));
		}
		ireader.close();

		return results;
	}

	private static Query constructLuceneQuery(Topic topic) throws ParseException {
		QueryParser parser = new QueryParser(TEXT_FIELD, new EnglishAnalyzer());
		Query summaryQuery = parser.parse(QueryParser.escape(topic.getSummary()));
		if (topic.getDiagnosis().isPresent()) {
			Query diagnosisQuery = parser.parse(QueryParser.escape(topic.getDiagnosis().get()));
			BooleanQuery.Builder queryBuilder = new BooleanQuery.Builder();
			queryBuilder.add(summaryQuery, BooleanClause.Occur.MUST);
			queryBuilder.add(diagnosisQuery, BooleanClause.Occur.MUST);
			return queryBuilder.build();
		} else {
			return summaryQuery;
		}
	}
}
