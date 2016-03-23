package ch.ethz.inf.da.cds.ir.util;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;

import ch.ethz.inf.da.cds.ir.FilePaths;

public class DocUtils {
	public static List<String> getValidDocIds() throws IOException {
		Path docIdsDir = FilePaths.DATA_DIR.resolve("doc-ids");
		List<String> validIds = FileUtils.readLines(docIdsDir.resolve("docnos-2014.txt").toFile());

		List<String> dup1 = FileUtils.readLines(docIdsDir.resolve("duplicates-1.txt").toFile());
		for (String filename : dup1) {
			validIds.remove(FilenameUtils.getBaseName(filename));
		}

		List<String> dup2 = FileUtils.readLines(docIdsDir.resolve("duplicates-2.txt").toFile());
		for (String line : dup2) {
			String[] filenames = line.split("\\s+");
			validIds.remove(FilenameUtils.getBaseName(filenames[1]));
			validIds.remove(FilenameUtils.getBaseName(filenames[2]));
		}

		return validIds;
	}

}
