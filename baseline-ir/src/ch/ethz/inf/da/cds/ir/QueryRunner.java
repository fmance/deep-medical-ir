package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;

import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.QrelUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

public class QueryRunner {
	private static final Path QUERIES_2014_FILE = FilePaths.DATA_DIR.resolve("topics-2014.xml");
	private static final Path RESULTS_2014_FILE = FilePaths.DATA_DIR.resolve("results-2014.txt");
	private static final Path QUERIES_2015_A_FILE = FilePaths.DATA_DIR.resolve("topics-2015-A.xml");
	private static final Path RESULTS_2015_A_FILE = FilePaths.DATA_DIR.resolve("results-2015-A.txt");
	private static final Path QUERIES_2015_B_FILE = FilePaths.DATA_DIR.resolve("topics-2015-B.xml");
	private static final Path RESULTS_2015_B_FILE = FilePaths.DATA_DIR.resolve("results-2015-B.txt");

	public static void main(String[] args) throws Exception {
		runQueries(QUERIES_2014_FILE.toFile(), RESULTS_2014_FILE.toFile(), false);
		runQueries(QUERIES_2015_A_FILE.toFile(), RESULTS_2015_A_FILE.toFile(), false);
		runQueries(QUERIES_2015_B_FILE.toFile(), RESULTS_2015_B_FILE.toFile(), false);
	}

	private static void runQueries(File queriesFile, File resultsFile, boolean filterKnownDocs2014) throws Exception {
		System.out.println("Running queries from " + queriesFile);

		Set<String> knownDocs2014 = QrelUtils.getQrels("../data/qrels2014.txt");
		int skipped = 0;

		List<Topic> topics = XmlUtils.parseTopics(queriesFile);
		PrintWriter pw = new PrintWriter(resultsFile);

		for (Topic topic : topics) {
			List<SearchResult> results = LuceneUtils.searchIndex(FilePaths.INDEX_DIR, topic);
			for (SearchResult result : results) {
				if (filterKnownDocs2014 && knownDocs2014.contains(result.getPmcid())) {
					skipped++;
					continue;
				}
				pw.println(topic.getId() + " Q0 " + result.getPmcid() + " " + result.getRank() + " " + result.getScore()
						+ " STANDARD");
			}
		}

		pw.close();

		System.out.println("Done" + (skipped > 0 ? (" skipped " + skipped + " known docs from 2014.") : "."));
	}
}
