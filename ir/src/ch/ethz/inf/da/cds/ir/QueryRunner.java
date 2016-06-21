package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.lucene.queryparser.classic.ParseException;

import ch.ethz.inf.da.cds.ir.TrecQuery.TYPE;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

import com.google.common.base.Optional;
import com.google.common.collect.Lists;

public class QueryRunner {
    public static final int NUM_SEARCH_RESULTS = 100;

    public static void main(String[] args) throws Exception {
        FilePaths.RESULTS_DIR.toFile().mkdir();
        String field = LuceneUtils.TEXT_FIELD;
        runQueriesFromXml(FilePaths.QUERIES_2014_FILE.toFile(), field, FilePaths.RESULTS_2014_FILE.toFile());
        runQueriesFromXml(FilePaths.QUERIES_2015_A_FILE.toFile(), field, FilePaths.RESULTS_2015_FILE.toFile());
        runQueriesFromPlaintext(FilePaths.QUERIES_2014_EXPANDED_FILE.toFile(),
                                field,
                                FilePaths.RESULTS_2014_EXPANDED_FILE.toFile());

        // runQueries(FilePaths.QUERIES_2015_B_FILE.toFile(), field,
        // FilePaths.RESULTS_2015_B_FILE.toFile());
    }

    private static void runQueriesFromXml(File queriesXmlFile, String field, File resultsFile) throws Exception {
        System.out.println("Running queries from " + queriesXmlFile);
        List<TrecQuery> queries = XmlUtils.parseQueries(queriesXmlFile);
        runTrecQueries(queries, field, resultsFile);
    }

    private static void runQueriesFromPlaintext(File queriesPlaintextFile, String field, File resultsFile)
            throws Exception {
        System.out.println("Running queries from " + queriesPlaintextFile);
        List<TrecQuery> queries = Lists.newArrayList();

        List<String> lines = FileUtils.readLines(queriesPlaintextFile);
        for (int qid = 1; qid <= 30; qid++) {
            TrecQuery.TYPE type = null;
            if (qid <= 10) {
                type = TYPE.DIAGNOSIS;
            } else if (qid <= 20) {
                type = TYPE.TEST;
            } else {
                type = TYPE.TREATMENT;
            }

            TrecQuery query = new TrecQuery(qid, type, " ", lines.get(qid - 1), Optional.absent());
            queries.add(query);
        }

        runTrecQueries(queries, field, resultsFile);
    }

    private static void runTrecQueries(List<TrecQuery> queries, String field, File resultsFile)
            throws FileNotFoundException, IOException, ParseException {
        PrintWriter pw = new PrintWriter(resultsFile);

        for (TrecQuery query : queries) {
            List<SearchResult> results = LuceneUtils.searchBM25Index(query, field, NUM_SEARCH_RESULTS);
            for (SearchResult result : results) {
                pw.println(query.getId() + " Q0 " + result.getPmcid() + " " + result.getRank() + " "
                           + result.getScore() + " STANDARD");
            }
        }

        pw.close();

        System.out.println("Done");
    }
}
