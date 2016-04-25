package ch.ethz.inf.da.cds.ir.util;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;

import ch.ethz.inf.da.cds.ir.FilePaths;

public class DocUtils {
    private static final Path DOC_IDS_PATH = FilePaths.DATA_DIR.resolve("doc-ids");

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

    public static void main(String[] args) throws IOException {
        PrintWriter pw = new PrintWriter(DOC_IDS_PATH.resolve("valid-doc-ids.txt").toFile());
        for (String did : getValidDocIds()) {
            pw.println(did);
        }
        pw.close();
    }

}
