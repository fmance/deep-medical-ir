package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.List;

import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

public class QueryRunner {
	private static final Path QUERIES_2014_FILE = FilePaths.DATA_DIR.resolve("topics-2014.xml");
	private static final Path RESULTS_2014_FILE = FilePaths.DATA_DIR.resolve("results-2014.txt");
	private static final Path QUERIES_2015_A_FILE = FilePaths.DATA_DIR.resolve("topics-2015-A.xml");
	private static final Path RESULTS_2015_A_FILE = FilePaths.DATA_DIR.resolve("results-2015-A.txt");
	private static final Path QUERIES_2015_B_FILE = FilePaths.DATA_DIR.resolve("topics-2015-B.xml");
	private static final Path RESULTS_2015_B_FILE = FilePaths.DATA_DIR.resolve("results-2015-B.txt");

	public static void main(String[] args) throws Exception {
		runQueries(QUERIES_2014_FILE.toFile(), RESULTS_2014_FILE.toFile());
		runQueries(QUERIES_2015_A_FILE.toFile(), RESULTS_2015_A_FILE.toFile());
		runQueries(QUERIES_2015_B_FILE.toFile(), RESULTS_2015_B_FILE.toFile());
	}

	private static void runQueries(File queriesFile, File resultsFile) throws Exception {
		System.out.println("Running queries from " + queriesFile);
		PrintWriter pw = new PrintWriter(resultsFile);

		List<Topic> topics = XmlUtils.parseTopics(queriesFile);
		for (Topic topic : topics) {
			List<SearchResult> results = LuceneUtils.searchIndex(FilePaths.INDEX_DIR, topic);
			for (SearchResult result : results) {
				pw.println(topic.getId() + " Q0 " + result.getPmcid() + " " + result.getRank() + " " + result.getScore()
						+ " STANDARD");
			}
		}

		pw.close();
		System.out.println("Done.");
	}
}
