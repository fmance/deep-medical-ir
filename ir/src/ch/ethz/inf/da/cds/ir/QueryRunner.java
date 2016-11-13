package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.List;

import org.apache.lucene.queryparser.classic.ParseException;

import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

public class QueryRunner {
    public static enum Target {
        SUMMARIES, DESCRIPTIONS, NOTES
    }

    public static final int NUM_SEARCH_RESULTS = 100;

    public static void main(String[] args) throws Exception {
        FilePaths.RESULTS_DIR.toFile().mkdir();
        String field = LuceneUtils.TEXT_FIELD;
        // runQueriesFromXml(FilePaths.QUERIES_2014_FILE.toFile(),
        // field,
        // FilePaths.RESULTS_2014_SUM_FILE.toFile(),
        // Target.SUMMARIES);
        // runQueriesFromXml(FilePaths.QUERIES_2014_FILE.toFile(),
        // field,
        // FilePaths.RESULTS_2014_DESC_FILE.toFile(),
        // Target.DESCRIPTIONS);
        // runQueriesFromXml(FilePaths.QUERIES_2015_A_FILE.toFile(),
        // field,
        // FilePaths.RESULTS_2015_SUM_FILE.toFile(),
        // Target.SUMMARIES);
        // runQueriesFromXml(FilePaths.QUERIES_2015_A_FILE.toFile(),
        // field,
        // FilePaths.RESULTS_2015_DESC_FILE.toFile(),
        // Target.DESCRIPTIONS);
        runQueriesFromXml(FilePaths.QUERIES_2016_FILE.toFile(),
                          field,
                          FilePaths.RESULTS_2016_SUM_FILE.toFile(),
                          Target.SUMMARIES);
        runQueriesFromXml(FilePaths.QUERIES_2016_FILE.toFile(),
                          field,
                          FilePaths.RESULTS_2016_DESC_FILE.toFile(),
                          Target.DESCRIPTIONS);
        runQueriesFromXml(FilePaths.QUERIES_2016_FILE.toFile(),
                          field,
                          FilePaths.RESULTS_2016_NOTE_FILE.toFile(),
                          Target.NOTES);

        // runQueriesFromPlaintext(FilePaths.QUERIES_2016_FILE.toFile(), field, FilePaths.RESULTS_2016_FILE.toFile());
        // runQueriesFromPlaintext(FilePaths.QUERIES_2015_EXPANDED_FILE.toFile(),
        // field,
        // FilePaths.RESULTS_2015_EXPANDED_FILE.toFile());

        // runQueries(FilePaths.QUERIES_2015_B_FILE.toFile(), field,
        // FilePaths.RESULTS_2015_B_FILE.toFile());
    }

    private static void runQueriesFromXml(File queriesXmlFile, String field, File resultsFile, Target target)
            throws Exception {
        System.out.println("Running queries from " + queriesXmlFile + " target = " + target);
        List<TrecQuery> queries = XmlUtils.parseQueries(queriesXmlFile);
        runTrecQueries(queries, field, resultsFile, target);
    }

    // private static void runQueriesFromPlaintext(File queriesPlaintextFile, String field, File resultsFile)
    // throws Exception {
    // System.out.println("Running queries from " + queriesPlaintextFile);
    // List<TrecQuery> queries = Lists.newArrayList();
    //
    // List<String> lines = FileUtils.readLines(queriesPlaintextFile);
    // for (int qid = 1; qid <= 30; qid++) {
    // TrecQuery.TYPE type = null;
    // if (qid <= 10) {
    // type = TYPE.DIAGNOSIS;
    // } else if (qid <= 20) {
    // type = TYPE.TEST;
    // } else {
    // type = TYPE.TREATMENT;
    // }
    //
    // TrecQuery query = new TrecQuery(qid, type, " ", lines.get(qid - 1), "", Optional.absent());
    // queries.add(query);
    // }
    //
    // runTrecQueries(queries, field, resultsFile, Target.SUMMARIES);
    // }

    private static void runTrecQueries(List<TrecQuery> queries, String field, File resultsFile, Target target)
            throws FileNotFoundException, IOException, ParseException {
        PrintWriter pw = new PrintWriter(resultsFile);

        for (TrecQuery query : queries) {
            String queryString = null;
            if (target == Target.SUMMARIES) {
                queryString = query.getSummary();
            } else if (target == Target.DESCRIPTIONS) {
                queryString = query.getDescription();
            } else {
                queryString = query.getNote();
            }
            List<SearchResult> results = LuceneUtils.searchBM25Index(queryString, field, NUM_SEARCH_RESULTS);
            // List<SearchResult> results = LuceneUtils.searchLMDirichletIndex(queryString, field, NUM_SEARCH_RESULTS);
            for (SearchResult result : results) {
                pw.println(query.getId() + " Q0 " + result.getPmcid() + " " + result.getRank() + " "
                           + result.getScore() + " STANDARD");
            }
        }

        pw.close();

        System.out.println("Done");
    }
}
