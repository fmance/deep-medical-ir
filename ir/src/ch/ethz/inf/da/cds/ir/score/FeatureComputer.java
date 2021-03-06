package ch.ethz.inf.da.cds.ir.score;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.tuple.Pair;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.store.NIOFSDirectory;

import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.QueryRunner;
import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.TrecQuery.TYPE;
import ch.ethz.inf.da.cds.ir.score.Scorer.Measure;
import ch.ethz.inf.da.cds.ir.util.DocUtils;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.QrelUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;
import com.google.common.primitives.Doubles;

public class FeatureComputer {
    private static final TYPE CLASS_ID = TrecQuery.TYPE.DIAGNOSIS;
    private static final List<String> CLASSIFIERS = Lists.newArrayList("SVMPerf.05.0.001.hedges");
    private static final String HEDGES = "";// "-hedges" or ""

    private static final Map<TYPE, String> CLASS_ID_TO_CLASSIFIER = ImmutableMap.of(TrecQuery.TYPE.DIAGNOSIS,
                                                                                    "diag",
                                                                                    TrecQuery.TYPE.TEST,
                                                                                    "diag",
                                                                                    TrecQuery.TYPE.TREATMENT,
                                                                                    "treat");
    private static final List<Map<Integer, Double>> CLASSIFICATION_SCORES_LIST = Lists.newArrayList();
    static {
        for (String classifierExt : CLASSIFIERS) {
            try {
                CLASSIFICATION_SCORES_LIST.add(getClassificationScores(classifierExt,
                                                                       CLASS_ID_TO_CLASSIFIER.get(CLASS_ID)));
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    public static void main(String[] args) throws Exception {
        IndexReader reader = DirectoryReader.open(NIOFSDirectory.open(FilePaths.BM25_INDEX_DIR));
        int[] docIdMapping = LuceneUtils.getLuceneToPmcIdMapping(reader);
        String field = LuceneUtils.TEXT_FIELD;

        writeTrain2014(reader, docIdMapping, field);

        // writeScores(reader,
        // docIdMapping,
        // field,
        // FilePaths.QUERIES_2014_FILE.toFile(),
        // FilePaths.BM25_SCORES_2014_FILE.toFile(),
        // Measure.BM25);
        //
        // writeScores(reader,
        // docIdMapping,
        // field,
        // FilePaths.QUERIES_2015_A_FILE.toFile(),
        // FilePaths.BM25_SCORES_2015_FILE.toFile(),
        // Measure.BM25);
        //
        // writeScores(reader,
        // docIdMapping,
        // field,
        // FilePaths.QUERIES_2014_FILE.toFile(),
        // FilePaths.TFIDF_SCORES_2014_FILE.toFile(),
        // Measure.TFIDF);
        //
        // writeScores(reader,
        // docIdMapping,
        // field,
        // FilePaths.QUERIES_2015_A_FILE.toFile(),
        // FilePaths.TFIDF_SCORES_2015_FILE.toFile(),
        // Measure.TFIDF);

        reader.close();
    }

    private static void writeTrain2014(IndexReader reader, int[] docIdMapping, String field) throws Exception {
        writeQrelsFeatures(reader,
                           docIdMapping,
                           field,
                           FilePaths.QUERIES_2014_FILE,
                           FilePaths.QRELS_2014,
                           FilePaths.FEATURES_2014,
                           Sets.newHashSet(17, 23, 25));
        writeResultsFeatures(reader,
                             docIdMapping,
                             field,
                             FilePaths.QUERIES_2015_A_FILE,
                             FilePaths.QRELS_2015,
                             FilePaths.FEATURES_2015);
    }

    private static void writeTrain2015(IndexReader reader, int[] docIdMapping, String field) throws Exception {
        writeQrelsFeatures(reader,
                           docIdMapping,
                           field,
                           FilePaths.QUERIES_2015_A_FILE,
                           FilePaths.QRELS_2015,
                           FilePaths.FEATURES_2015,
                           Sets.newHashSet(5, 20, 25));
        writeResultsFeatures(reader,
                             docIdMapping,
                             field,
                             FilePaths.QUERIES_2014_FILE,
                             FilePaths.QRELS_2014,
                             FilePaths.FEATURES_2014);
    }

    private static void writeScores(IndexReader reader,
                                    int[] docIdMapping,
                                    String field,
                                    File queriesFile,
                                    File resultsFile,
                                    Measure measure) throws Exception {
        List<TrecQuery> trecQueries = XmlUtils.parseQueries(queriesFile);
        PrintWriter pw = new PrintWriter(resultsFile);

        long begin = System.currentTimeMillis();
        for (TrecQuery trecQuery : trecQueries) {
            int queryId = trecQuery.getId();
            System.out.println("Scoring query " + queryId);
            Features[] features = Scorer.getFeatures(field, trecQuery, reader);
            Scorer.writeTopScores(features, queryId, QueryRunner.NUM_SEARCH_RESULTS, pw, docIdMapping, measure);

        }

        long end = System.currentTimeMillis();
        System.out.println((end - begin) / 1e3);

        pw.close();
    }

    private static void writeResultsFeatures(IndexReader reader,
                                             int[] docIdMapping,
                                             String field,
                                             Path queriesFile,
                                             Path qrelsFile,
                                             Path featuresFile) throws Exception {
        List<TrecQuery> trecQueries = XmlUtils.parseQueries(queriesFile.toFile());
        Map<Pair<Integer, Integer>, Integer> relevances = QrelUtils.getRelevance(qrelsFile);

        PrintWriter pw = new PrintWriter(featuresFile.toFile());
        PrintWriter docIdPw = new PrintWriter(featuresFile.toString() + ".doc-ids.txt");

        long begin = System.currentTimeMillis();
        for (TrecQuery trecQuery : trecQueries) {
            if (trecQuery.getType() != CLASS_ID) {
                continue;
            }

            int queryId = trecQuery.getId();
            System.out.println("Scoring query " + queryId);
            Features[] features = Scorer.getFeatures(field, trecQuery, reader);
            Set<Integer> topDocs = Scorer.getTopDocs(features, 100, Measure.BM25).keySet();

            for (int docId = 0; docId < features.length; docId++) {
                int pmcid = docIdMapping[docId];
                Integer relevance = relevances.get(Pair.of(queryId, pmcid));
                if (!topDocs.contains(docId)) {
                    continue;
                }
                if (relevance == null) {
                    relevance = 0;
                }

                writeFeaturesForQueryDocPair(pw, docIdPw, features, queryId, pmcid, relevance, docId);
            }

        }

        long end = System.currentTimeMillis();
        System.out.println((end - begin) / 1e3);

        pw.close();
        docIdPw.close();
    }

    private static void writeQrelsFeatures(IndexReader reader,
                                           int[] docIdMapping,
                                           String field,
                                           Path queriesFile,
                                           Path qrelsFile,
                                           Path featuresFile,
                                           Set<Integer> queryIdBlacklist) throws Exception {
        List<TrecQuery> trecQueries = XmlUtils.parseQueries(queriesFile.toFile());
        List<Integer> validDocIds = DocUtils.getValidDocIds()
                                            .stream()
                                            .map(s -> Integer.parseInt(s))
                                            .collect(Collectors.toList());

        Map<Pair<Integer, Integer>, Integer> relevances = QrelUtils.getRelevance(qrelsFile);
        Map<Integer, Integer> reverseDocIdMapping = getReverseMapping(docIdMapping);

        PrintWriter pw = new PrintWriter(featuresFile.toFile());
        PrintWriter docIdPw = new PrintWriter(featuresFile.toString() + ".doc-ids.txt");

        long begin = System.currentTimeMillis();
        for (TrecQuery trecQuery : trecQueries) {
            if (trecQuery.getType() != CLASS_ID) {
                continue;
            }
            if (queryIdBlacklist.contains(trecQuery.getId())) {
                continue;
            }

            System.out.println("Scoring query " + trecQuery.getId());
            Features[] features = Scorer.getFeatures(field, trecQuery, reader);
            int positive = 0;
            for (Map.Entry<Pair<Integer, Integer>, Integer> relevanceEntry : relevances.entrySet()) {
                int queryId = relevanceEntry.getKey().getLeft();
                int pmcid = relevanceEntry.getKey().getRight();
                int relevance = relevanceEntry.getValue();
                if (queryId != trecQuery.getId() || !validDocIds.contains(pmcid)) {
                    continue;
                }
                if (relevance > 0) {
                    positive++;
                }
            }
            System.out.println("positives : " + positive);

            for (Map.Entry<Pair<Integer, Integer>, Integer> relevanceEntry : relevances.entrySet()) {
                int queryId = relevanceEntry.getKey().getLeft();
                int pmcid = relevanceEntry.getKey().getRight();
                int relevance = relevanceEntry.getValue();
                if (queryId != trecQuery.getId() || !validDocIds.contains(pmcid)) {
                    continue;
                }
                if (relevance == 0 && positive == 0) {
                    continue;
                }

                Integer docId = reverseDocIdMapping.get(pmcid);
                boolean negativeWritten = writeFeaturesForQueryDocPair(pw,
                                                                       docIdPw,
                                                                       features,
                                                                       queryId,
                                                                       pmcid,
                                                                       relevance,
                                                                       docId);
                if (negativeWritten) {
                    positive--;
                }
            }

        }

        long end = System.currentTimeMillis();
        System.out.println((end - begin) / 1e3);

        pw.close();
        docIdPw.close();
    }

    private static boolean writeFeaturesForQueryDocPair(PrintWriter pw,
                                                        PrintWriter docIdPw,
                                                        Features[] features,
                                                        int queryId,
                                                        int pmcid,
                                                        int relevance,
                                                        Integer docId) throws Exception {
        List<Double> scores = Lists.newArrayList();
        for (Map<Integer, Double> classificationScores : CLASSIFICATION_SCORES_LIST) {
            Double classificationScore = classificationScores.get(pmcid);
            if (classificationScore == null) {
                if (relevance > 0) {
                    throw new Exception("Did not find classify score for " + pmcid);
                } else {
                    return false;
                }
            }
            scores.add(classificationScore);
        }

        if (relevance == 2) {
            relevance = 1;
        }
        pw.printf("%d qid:%d ", relevance, queryId);

        int featureId = 1;
        for (Double score : scores) {
            pw.printf("%d:%f ", featureId++, score);
        }

        for (double feature : features[docId].toList()) {
            pw.printf("%d:%f ", featureId++, 3 * feature);
        }

        pw.printf("# %d\n", pmcid);

        docIdPw.println(pmcid);

        if (relevance == 0) {
            return true; // negative written
        } else {
            return false;
        }
    }

    private static Map<Integer, Integer> getReverseMapping(int[] docIdMapping) {
        Map<Integer, Integer> reverseMap = Maps.newHashMap();
        for (int i = 0; i < docIdMapping.length; i++) {
            reverseMap.put(docIdMapping[i], i);
        }
        return reverseMap;
    }

    private static Map<Integer, Double> getClassificationScores(String classifierExt, String category)
            throws IOException {
        Path root = FilePaths.ROOT_DIR.resolve("classification/data/res-and-qrels");
        List<String> ids = FileUtils.readLines(root.resolve("ids.txt").toFile());
        Path resultsDir = Paths.get(root.toString() + HEDGES).resolve("results").resolve(category);
        List<String> scoreLines = FileUtils.readLines(resultsDir.resolve("results.txt." + classifierExt).toFile());
        Map<Integer, Double> scores = Maps.newHashMap();
        for (int i = 0; i < ids.size(); i++) {
            int pmcid = Integer.parseInt(ids.get(i));
            double score = Double.parseDouble(scoreLines.get(i));
            scores.put(pmcid, score);
        }
        return scores;
    }

    private static void normalizeScores(double[] scores) {
        double maxScore = Doubles.max(scores);
        for (int i = 0; i < scores.length; i++) {
            scores[i] /= maxScore;
        }
    }

    private static double[] addScores(double[]... scores) {
        double[] result = new double[scores[0].length];
        for (int i = 0; i < result.length; i++) {
            for (int k = 0; k < scores.length; k++) {
                result[i] += scores[k][i];
            }
        }
        return result;
    }
}
