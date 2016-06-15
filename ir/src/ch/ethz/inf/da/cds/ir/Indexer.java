package ch.ethz.inf.da.cds.ir;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;
import org.apache.lucene.index.IndexWriter;

import ch.ethz.inf.da.cds.ir.util.DocUtils;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.ThreadUtils;

import com.google.common.base.Joiner;
import com.google.common.collect.Maps;

/**
 * Index the articles in the plaintext files to Lucene.
 * 
 * @author fmance
 *
 */
public class Indexer {
    private static final int INDEXER_THREAD_POOL_SIZE = 4;
    private static final List<String> VALID_DOC_IDS = DocUtils.getValidDocIds();

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

    public static void main(String[] args) throws Exception {
        // String parsePlaintextFile =
        // IndexerThread.parsePlaintextFile("2113833");
        // System.out.println(parsePlaintextFile);

        for (String dir : new String[] { "00", "01", "02", "03" }) {
            indexDirectory(FilePaths.PLAINTEXT_DIR.resolve(dir));
        }
    }

    private static void indexDirectory(Path directory) throws Exception {
        System.out.println("Indexing " + directory.normalize());
        long begin = System.currentTimeMillis();

        File[] subdirs = directory.toFile().listFiles();
        Arrays.sort(subdirs);

        IndexWriter indexWriter = LuceneUtils.getBM25IndexWriter();

        ExecutorService executor = Executors.newFixedThreadPool(INDEXER_THREAD_POOL_SIZE);
        for (File subdir : subdirs) {
            executor.submit(new IndexerThread(subdir, indexWriter));
        }
        ThreadUtils.shutdownExecutor(executor);

        System.out.println("\nClosing index...\n");
        indexWriter.close();

        double took = (System.currentTimeMillis() - begin) / (1e3 * 60);
        System.out.println("\nIndexed " + directory.normalize() + ", took " + took + " min.\n");
    }

    static class IndexerThread implements Runnable {
        private final File directory;
        private final IndexWriter indexWriter;

        public IndexerThread(File directory, IndexWriter indexWriter) {
            this.directory = directory;
            this.indexWriter = indexWriter;
        }

        @Override
        public void run() {
            System.out.println("Indexing directory " + directory.toPath().normalize());
            long start = System.currentTimeMillis();

            for (File articleFile : directory.listFiles()) {
                if (!articleFile.getName().endsWith(".txt")) {
                    continue;
                }
                try {
                    String pmcid = FilenameUtils.getBaseName(articleFile.getName());
                    if (!VALID_DOC_IDS.contains(pmcid)) {
                        continue;
                    }
                    List<String> lines = FileUtils.readLines(articleFile);
                    String title = lines.get(0);
                    String text;
                    if (PLAINTEXT_PATH_MAP.containsKey(pmcid)) {
                        text = parsePlaintextFile(pmcid);
                    } else {
                        text = Joiner.on("\n").join(lines.subList(1, lines.size()));
                    }
                    LuceneUtils.index(indexWriter, new Article(pmcid, title, text));

                } catch (Throwable e) {
                    e.printStackTrace();
                }
            }

            double took = (System.currentTimeMillis() - start) / 1e3;
            System.out.println("\nFinished indexing " + directory.toPath().normalize() + " took " + took + " sec.");
        }

        private static String parsePlaintextFile(String pmcid) throws IOException, FileNotFoundException {
            // Pattern pattern = Pattern.compile("==== Refs",
            // Pattern.CASE_INSENSITIVE);

            StringBuilder text = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new FileReader(PLAINTEXT_PATH_MAP.get(pmcid).toFile()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    if (line.matches("==== Refs") || line.equals("References") || line.equals("REFERENCES")) {
                        break;
                    }
                    text.append(line);
                    text.append('\n');
                }
            }
            return text.toString();
        }
    }
}
