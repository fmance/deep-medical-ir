package ch.ethz.inf.da.cds.ir;

import java.nio.file.Path;
import java.nio.file.Paths;

public class FilePaths {
    public static final Path ROOT_DIR = Paths.get("..");
    public static final Path DATA_DIR = ROOT_DIR.resolve("data");
    public static final Path XML_DIR = DATA_DIR.resolve("xml");
    public static final Path PLAINTEXT_DIR = DATA_DIR.resolve("plaintext");

    public static final Path QRELS_DIR = DATA_DIR.resolve("qrels");
    public static final Path QRELS_2014 = QRELS_DIR.resolve("qrels-treceval-2014.txt");
    public static final Path QRELS_2015 = QRELS_DIR.resolve("qrels-treceval-2015.txt");

    public static final Path QUERIES_DIR = DATA_DIR.resolve("queries");
    public static final Path QUERIES_2014_FILE = QUERIES_DIR.resolve("topics-2014.xml");
    public static final Path QUERIES_2015_A_FILE = QUERIES_DIR.resolve("topics-2015-A.xml");
    public static final Path QUERIES_2015_B_FILE = QUERIES_DIR.resolve("topics-2015-B.xml");
    public static final Path QUERIES_2014_PLAINTEXT_FILE = QUERIES_DIR.resolve("topics-2014.txt");
    public static final Path QUERIES_2015_A_PLAINTEXT_FILE = QUERIES_DIR.resolve("topics-2015-A.txt");
    public static final Path QUERIES_2015_B_PLAINTEXT_FILE = QUERIES_DIR.resolve("topics-2015-B.txt");
    public static final Path QUERIES_2014_EXPANDED_FILE = QUERIES_DIR.resolve("topics-2014-exp.txt");
    public static final Path QUERIES_2015_EXPANDED_FILE = QUERIES_DIR.resolve("topics-2015-exp.txt");
    public static final Path QUERIES_2016_FILE = QUERIES_DIR.resolve("topics-2016.txt");

    public static final Path RESULTS_DIR = Paths.get("results");
    public static final Path RESULTS_2014_FILE = FilePaths.RESULTS_DIR.resolve("results-2014.txt");
    public static final Path RESULTS_2015_FILE = FilePaths.RESULTS_DIR.resolve("results-2015.txt");
    public static final Path RESULTS_2015_B_FILE = FilePaths.RESULTS_DIR.resolve("results-2015-B.txt");
    public static final Path RESULTS_2016_FILE = FilePaths.RESULTS_DIR.resolve("results-2016-exp-sum.txt");

    public static final Path RESULTS_2014_EXPANDED_FILE = FilePaths.RESULTS_DIR.resolve("results-2014-expanded.txt");
    public static final Path RESULTS_2015_EXPANDED_FILE = FilePaths.RESULTS_DIR.resolve("results-2015-expanded.txt");

    public static final Path BM25_SCORES_2014_FILE = RESULTS_DIR.resolve("bm25-scores-2014.txt");
    public static final Path BM25_SCORES_2015_FILE = RESULTS_DIR.resolve("bm25-scores-2015.txt");
    public static final Path TFIDF_SCORES_2014_FILE = RESULTS_DIR.resolve("tfidf-scores-2014.txt");
    public static final Path TFIDF_SCORES_2015_FILE = RESULTS_DIR.resolve("tfidf-scores-2015.txt");

    public static final Path FEATURES_2014 = RESULTS_DIR.resolve("features-2014.txt");
    public static final Path FEATURES_2015 = RESULTS_DIR.resolve("features-2015.txt");

    public static final Path BM25_INDEX_DIR = Paths.get("index");
}
