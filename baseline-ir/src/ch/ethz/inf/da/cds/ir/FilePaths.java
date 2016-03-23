package ch.ethz.inf.da.cds.ir;

import java.nio.file.Path;
import java.nio.file.Paths;

public class FilePaths {
	public static final Path DATA_DIR = Paths.get("../data/");

	public static final Path PMC_00_DIR = DATA_DIR.resolve("pmc-text-00");
	public static final Path PMC_01_DIR = DATA_DIR.resolve("pmc-text-01");
	public static final Path PMC_02_DIR = DATA_DIR.resolve("pmc-text-02");
	public static final Path PMC_03_DIR = DATA_DIR.resolve("pmc-text-03");

	public static final Path PLAINTEXT_DIR = DATA_DIR.resolve("plaintext");
	public static final Path PLAINTEXT_DIR_03 = PLAINTEXT_DIR.resolve("03");
	public static final Path PLAINTEXT_DIR_02 = PLAINTEXT_DIR.resolve("02");
	public static final Path PLAINTEXT_DIR_01 = PLAINTEXT_DIR.resolve("01");
	public static final Path PLAINTEXT_DIR_00 = PLAINTEXT_DIR.resolve("00");

	public static final Path INDEX_DIR = Paths.get("index");
}
