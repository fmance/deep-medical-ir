package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

import org.apache.commons.io.FilenameUtils;
import org.apache.lucene.index.IndexWriter;

import ch.ethz.inf.da.cds.ir.util.DocUtils;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.ThreadUtils;

import com.google.common.base.Joiner;

/**
 * Index the articles in the plaintext files to Lucene.
 * 
 * @author fmance
 *
 */
public class Indexer {
    private static final int INDEXER_THREAD_POOL_SIZE = 4;
    private static final List<String> VALID_DOC_IDS = DocUtils.getValidDocIds();
    private static AtomicInteger plaintext = new AtomicInteger();

    public static void main(String[] args) throws Exception {
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
        System.out.println("\nIndexed " + directory.normalize() + ", took " + took + " min, plaintext = " + plaintext
                           + "\n\n");
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
                    Path fileToIndex = DocUtils.getFullTextPath(articleFile.toPath());
                    if (!fileToIndex.equals(articleFile.toPath())) {
                        plaintext.incrementAndGet();
                    }
                    List<String> lines = Files.readAllLines(fileToIndex);
                    String title = lines.get(0);
                    String text = Joiner.on("\n").join(lines);
                    LuceneUtils.index(indexWriter, new Article(pmcid, title, text));
                } catch (Throwable e) {
                    e.printStackTrace();
                }
            }

            double took = (System.currentTimeMillis() - start) / 1e3;
            System.out.println("\nFinished indexing " + directory.toPath().normalize() + " took " + took
                               + " sec, plaintext = " + plaintext);
        }
    }
}
