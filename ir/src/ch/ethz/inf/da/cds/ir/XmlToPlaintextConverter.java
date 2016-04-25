package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.xml.parsers.ParserConfigurationException;

import org.xml.sax.SAXException;

import ch.ethz.inf.da.cds.ir.util.DocUtils;
import ch.ethz.inf.da.cds.ir.util.ThreadUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

/**
 * Convert the XML files in the PMC directories into plaintext files.
 * 
 * @author fmance
 *
 */
public class XmlToPlaintextConverter {
    private static final int WRITER_THREAD_POOL_SIZE = 6;

    public static void main(String[] args) throws Exception {
        List<String> validIds = DocUtils.getValidDocIds();
        FilePaths.PLAINTEXT_DIR.toFile().mkdir();
        convertPmcDirectory(FilePaths.PMC_00_DIR.toFile(), FilePaths.PLAINTEXT_DIR_00.toFile(), validIds);
        convertPmcDirectory(FilePaths.PMC_01_DIR.toFile(), FilePaths.PLAINTEXT_DIR_01.toFile(), validIds);
        convertPmcDirectory(FilePaths.PMC_02_DIR.toFile(), FilePaths.PLAINTEXT_DIR_02.toFile(), validIds);
        convertPmcDirectory(FilePaths.PMC_03_DIR.toFile(), FilePaths.PLAINTEXT_DIR_03.toFile(), validIds);
        convertQuerySummaries(FilePaths.QUERIES_2014_FILE.toFile(),
                FilePaths.QUERIES_2014_PLAINTEXT_FILE.toFile());
        convertQuerySummaries(FilePaths.QUERIES_2015_A_FILE.toFile(),
                FilePaths.QUERIES_2015_A_PLAINTEXT_FILE.toFile());
    }

    private static void convertPmcDirectory(File pmcDir, File plaintextDir, List<String> validDocIds)
            throws Exception {
        System.out.println("Converting " + pmcDir.toPath().normalize() + "\n");
        long begin = System.currentTimeMillis();

        plaintextDir.mkdir();
        File[] subdirs = pmcDir.listFiles();
        Arrays.sort(subdirs);

        ExecutorService executor = Executors.newFixedThreadPool(WRITER_THREAD_POOL_SIZE);
        for (File subdir : subdirs) {
            executor.submit(new ConverterThread(subdir, plaintextDir.toPath().resolve(subdir.getName())
                    .toFile(), validDocIds));
        }
        ThreadUtils.shutdownExecutor(executor);

        long end = System.currentTimeMillis();
        System.out.println("Converted " + pmcDir.toPath().normalize() + ", took " + (end - begin)
                / (1e3 * 60) + " minutes\n\n");
    }

    static class ConverterThread implements Runnable {
        private final File srcDir;
        private final File destDir;
        private final List<String> validDocIds;

        public ConverterThread(File srcDir, File destDir, List<String> validDocIds) {
            this.srcDir = srcDir;
            this.destDir = destDir;
            this.validDocIds = validDocIds;
        }

        @Override
        public void run() {
            System.out.println("Converting directory " + srcDir.toPath().normalize() + " to plaintext in "
                    + destDir.getAbsolutePath());
            long start = System.currentTimeMillis();

            destDir.mkdir();
            int filesWritten = 0;
            for (File articleFile : srcDir.listFiles()) {
                if (!articleFile.getName().endsWith(".nxml")) {
                    continue;
                }
                try {
                    Article article = XmlUtils.parseArticle(articleFile);
                    if (validDocIds.contains(article.getPmcid())) {
                        File textFile = destDir.toPath().resolve(article.getPmcid() + ".txt").toFile();
                        PrintWriter pw = new PrintWriter(textFile);
                        pw.println(article.getTitle());
                        pw.println(article.getText());
                        pw.close();
                        filesWritten++;
                    } else {
                        System.out.println("Ignoring invalid or duplicate article "
                                + articleFile.toPath().normalize());
                    }
                } catch (Throwable e) {
                    e.printStackTrace();
                }
                if (filesWritten % 500 == 0) {
                    long current = System.currentTimeMillis();
                    System.out.println("Directory " + srcDir.toPath().normalize() + ": written "
                            + filesWritten + " files, took " + (current - start) / 1e3 + " seconds.");
                }
            }

            long end = System.currentTimeMillis();
            System.out.println("\nFinished writing " + srcDir.toPath().normalize() + " " + filesWritten
                    + " files, took " + (end - start) / (1e3 * 60) + " minutes.\n");
        }
    }

    private static void convertQuerySummaries(File xmlQueryFile, File plaintextQueryFile)
            throws ParserConfigurationException, SAXException, IOException {
        List<TrecQuery> queries = XmlUtils.parseQueries(xmlQueryFile);
        PrintWriter pw = new PrintWriter(plaintextQueryFile);
        for (TrecQuery query : queries) {
            pw.printf("%d %s\n", query.getId(), query.getSummary());
        }
        pw.close();
    }
}
