package ch.ethz.inf.da.cds.ir.util;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;

import ch.ethz.inf.da.cds.ir.FilePaths;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

public class DocUtils {
    private static final Path DOC_IDS_PATH = FilePaths.DATA_DIR.resolve("doc-ids");

    private static final Map<String, Path> PLAINTEXT_PATH_MAP = Maps.newHashMap();
    static {
        try {
            List<String> lines = FileUtils.readLines(FilePaths.DATA_DIR.resolve("doc-ids")
                                                                       .resolve("pdf-only-path-map.txt")
                                                                       .toFile());
            for (String line : lines) {
                String[] parts = line.split("\\s+");
                PLAINTEXT_PATH_MAP.put(parts[0], Paths.get(parts[1]));
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static List<String> getValidDocIds() {
        try {
            List<String> validIds = FileUtils.readLines(DOC_IDS_PATH.resolve("docnos-2014.txt").toFile());

            List<String> dup1 = FileUtils.readLines(DOC_IDS_PATH.resolve("duplicates-1.txt").toFile());
            for (String filename : dup1) {
                validIds.remove(FilenameUtils.getBaseName(filename));
            }

            List<String> dup2 = FileUtils.readLines(DOC_IDS_PATH.resolve("duplicates-2.txt").toFile());
            for (String line : dup2) {
                String[] filenames = line.split("\\s+");
                validIds.remove(FilenameUtils.getBaseName(filenames[1]));
                validIds.remove(FilenameUtils.getBaseName(filenames[2]));
            }

            return validIds;
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    public static List<String> getValidDocIds2016() {
        List<String> validDocIds2016 = Lists.newArrayList();
        for (File dir : FilePaths.PLAINTEXT_DIR.toFile().listFiles()) {
            for (File subdir : dir.listFiles()) {
                for (File file : subdir.listFiles()) {
                    if (file.getName().endsWith(".txt")) {
                        validDocIds2016.add(FilenameUtils.getBaseName(file.getName()));
                    }
                }
            }
        }
        return validDocIds2016;
    }

    public static Path getFullTextPath(Path original) {
        Path full = Paths.get(original.toAbsolutePath().toString() + ".full");
        return Files.exists(full) ? full : original;
    }

    public static void main(String[] args) throws IOException {
        PrintWriter pw = new PrintWriter(DOC_IDS_PATH.resolve("valid-doc-ids-2016.txt").toFile());
        for (String did : getValidDocIds2016()) {
            pw.println(did);
        }
        pw.close();
    }

}
