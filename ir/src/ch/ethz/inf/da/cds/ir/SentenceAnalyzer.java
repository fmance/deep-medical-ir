package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.en.EnglishAnalyzer;

import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

import com.google.common.base.Joiner;

public class SentenceAnalyzer {
    private static final Path SENTENCES_DIR = FilePaths.ROOT_DIR.resolve("classification")
                                                                .resolve("data")
                                                                .resolve("sentences");
    private static final Analyzer analyzer = new EnglishAnalyzer();

    public static void main(String[] args) throws Exception {
        analyzeDirectory(SENTENCES_DIR.resolve("00").toFile());
        analyzeDirectory(SENTENCES_DIR.resolve("01").toFile());
        analyzeDirectory(SENTENCES_DIR.resolve("02").toFile());
        analyzeDirectory(SENTENCES_DIR.resolve("03").toFile());

    }

    private static void analyzeDirectory(File directory) throws Exception {
        System.out.println("Analyzing " + directory.toPath().normalize() + "\n");
        long begin = System.currentTimeMillis();

        File[] subdirs = directory.listFiles();
        Arrays.sort(subdirs);

        for (File subdir : subdirs) {
            analyzeSubdirectory(subdir);
        }

        long end = System.currentTimeMillis();
        System.out.println("\nAnalyzed " + directory.toPath().normalize() + ", took " + (end - begin)
                / (1e3 * 60) + " minutes\n\n");
    }

    private static void analyzeSubdirectory(File directory) {
        System.out.println("Analyzing directory " + directory.toPath().normalize());
        long start = System.currentTimeMillis();

        for (File articleFile : directory.listFiles()) {
            if (!articleFile.getName().endsWith(".txt.sent")) {
                continue;
            }
            try {
                // String pmcid =
                // FilenameUtils.getBaseName(articleFile.getName());
                List<String> lines = FileUtils.readLines(articleFile);
                String text = Joiner.on(" ").join(lines);
                List<String> analyzedText = LuceneUtils.tokenizeString(analyzer, text);
                FileUtils.write(new File(articleFile.getAbsolutePath() + ".analyzed"),
                                Joiner.on(" ").join(analyzedText));
            } catch (Throwable e) {
                e.printStackTrace();
            }
        }

        long end = System.currentTimeMillis();
        System.out.println("\nFinished analyzing " + directory.toPath().normalize() + " took "
                + (end - start) / (1e3 * 60) + " minutes.\n");
    }

}
