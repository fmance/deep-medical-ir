package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.en.EnglishAnalyzer;

import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

public class PlaintextAnalyzer {
    private static final Path ANALYZED_DIR = FilePaths.ROOT_DIR.resolve("classification")
                                                               .resolve("data")
                                                               .resolve("analyzed");
    private static final Analyzer ANALYZER = new EnglishAnalyzer();

    public static void main(String[] args) throws Exception {
        ANALYZED_DIR.toFile().mkdir();
        analyzeDirectory(FilePaths.PLAINTEXT_DIR_00.toFile(), ANALYZED_DIR.resolve("00").toFile());
        analyzeDirectory(FilePaths.PLAINTEXT_DIR_01.toFile(), ANALYZED_DIR.resolve("01").toFile());
        analyzeDirectory(FilePaths.PLAINTEXT_DIR_02.toFile(), ANALYZED_DIR.resolve("02").toFile());
        analyzeDirectory(FilePaths.PLAINTEXT_DIR_03.toFile(), ANALYZED_DIR.resolve("03").toFile());
    }

    private static void analyzeDirectory(File srcDir, File destDir) throws Exception {
        System.out.println("Analyzing " + srcDir.toPath().normalize() + "\n");
        long begin = System.currentTimeMillis();

        destDir.mkdir();

        File[] subdirs = srcDir.listFiles();
        Arrays.sort(subdirs);

        for (File subdir : subdirs) {
            analyzeSubdirectory(subdir, destDir.toPath().resolve(subdir.getName()).toFile());
        }

        long end = System.currentTimeMillis();
        System.out.println("\nAnalyzed " + srcDir.toPath().normalize() + ", took " + (end - begin)
                / (1e3 * 60) + " minutes\n\n");
    }

    private static void analyzeSubdirectory(File srcSubdir, File destSubdir) {
        System.out.println("Analyzing subdirectory " + srcSubdir.toPath().normalize());
        long start = System.currentTimeMillis();

        destSubdir.mkdir();

        for (File articleFile : srcSubdir.listFiles()) {
            if (!articleFile.getName().endsWith(".txt")) {
                continue;
            }
            try {
                List<String> lines = FileUtils.readLines(articleFile);
                StringBuilder analyzedText = new StringBuilder();
                for (String line : lines) {
                    // remove non-latin characters
                    String filtered = line.replaceAll("\\P{L}", " ");
                    List<String> tokens = LuceneUtils.tokenizeString(ANALYZER, filtered);
                    for (String token : tokens) {
                        analyzedText.append(token);
                        analyzedText.append(" ");
                    }
                    analyzedText.append("\n");
                }

                String pmcid = FilenameUtils.getBaseName(articleFile.getName());
                File outFile = destSubdir.toPath().resolve(pmcid + ".txt").toFile();
                FileUtils.write(outFile, analyzedText.toString());
            } catch (Throwable e) {
                e.printStackTrace();
            }
        }

        long end = System.currentTimeMillis();
        System.out.println("\nFinished analyzing " + srcSubdir.toPath().normalize() + " took "
                + (end - start) / (1e3 * 60) + " minutes.\n");
    }
}
