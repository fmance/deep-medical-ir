package ch.ethz.inf.da.cds.ir.convert;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.en.EnglishAnalyzer;

import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.util.DocUtils;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;

public class AnalyzerConverter {
    private static final Analyzer ENGLISH_ANALYZER = new EnglishAnalyzer();

    public static void main(String[] args) throws Exception {
        Path destRootDir = FilePaths.DATA_DIR.resolve("analyzed/analyzed-2016");
        destRootDir.toFile().mkdir();
        ConverterUtils.convert(FilePaths.PLAINTEXT_DIR_2016, destRootDir, AnalyzerConverter::analyzeFile);
    }

    private static Optional<String> analyzeFile(File file) {
        if (!file.getName().endsWith(".txt")) {
            return Optional.empty();
        }

        try {
            Path fileToAnalyze = DocUtils.getFullTextPath(file.toPath());
            List<String> lines = Files.readAllLines(fileToAnalyze);
            StringBuilder analyzedText = new StringBuilder();
            for (String line : lines) {
                // remove non-latin characters
                String filtered = line.replaceAll("\\P{L}", " ");
                List<String> tokens = LuceneUtils.tokenizeString(ENGLISH_ANALYZER, filtered);
                for (String token : tokens) {
                    analyzedText.append(token);
                    analyzedText.append(" ");
                }
                analyzedText.append("\n");
            }
            return Optional.of(analyzedText.toString());
        } catch (Throwable e) {
            e.printStackTrace();
            return Optional.empty();
        }
    }
}
