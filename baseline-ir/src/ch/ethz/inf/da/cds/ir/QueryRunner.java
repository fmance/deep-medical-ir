package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.io.PrintWriter;
import java.util.List;

import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

public class QueryRunner {
    private static final int NUM_SEARCH_RESULTS = 1000;

    public static void main(String[] args) throws Exception {
        FilePaths.RESULTS_DIR.toFile().mkdir();
        runQueries(FilePaths.QUERIES_2014_FILE.toFile(), FilePaths.RESULTS_2014_FILE.toFile());
        runQueries(FilePaths.QUERIES_2015_A_FILE.toFile(), FilePaths.RESULTS_2015_A_FILE.toFile());
        runQueries(FilePaths.QUERIES_2015_B_FILE.toFile(), FilePaths.RESULTS_2015_B_FILE.toFile());
    }

    private static void runQueries(File queriesFile, File resultsFile) throws Exception {
        System.out.println("Running queries from " + queriesFile);

        List<TrecQuery> queries = XmlUtils.parseQueries(queriesFile);
        PrintWriter pw = new PrintWriter(resultsFile);

        for (TrecQuery query : queries) {
            List<SearchResult> results = LuceneUtils.searchIndex(FilePaths.INDEX_DIR, query,
                    NUM_SEARCH_RESULTS);
            for (SearchResult result : results) {
                pw.println(query.getId() + " Q0 " + result.getPmcid() + " " + result.getRank() + " "
                        + result.getScore() + " STANDARD");
            }
        }

        pw.close();

        System.out.println("Done");
    }
}
