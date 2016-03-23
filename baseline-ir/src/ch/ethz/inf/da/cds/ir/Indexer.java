package ch.ethz.inf.da.cds.ir;

import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;
import org.apache.lucene.index.IndexWriter;

import com.google.common.base.Joiner;

import ch.ethz.inf.da.cds.ir.util.DocUtils;
import ch.ethz.inf.da.cds.ir.util.LuceneUtils;
import ch.ethz.inf.da.cds.ir.util.ThreadUtils;

/**
 * Index the articles in the plaintext files to Lucene.
 * 
 * @author fmance
 *
 */
public class Indexer {
	private static final int INDEXER_THREAD_POOL_SIZE = 6;

	public static void main(String[] args) throws Exception {
		List<String> validIds = DocUtils.getValidDocIds();
		indexDirectory(FilePaths.PLAINTEXT_DIR_00.toFile(), validIds);
		indexDirectory(FilePaths.PLAINTEXT_DIR_01.toFile(), validIds);
		indexDirectory(FilePaths.PLAINTEXT_DIR_02.toFile(), validIds);
		indexDirectory(FilePaths.PLAINTEXT_DIR_03.toFile(), validIds);
	}

	private static void indexDirectory(File directory, List<String> validDocIds) throws Exception {
		System.out.println("Indexing " + directory.toPath().normalize() + "\n");
		long begin = System.currentTimeMillis();

		File[] subdirs = directory.listFiles();
		Arrays.sort(subdirs);

		IndexWriter indexWriter = LuceneUtils.getIndexWriter(FilePaths.INDEX_DIR);

		ExecutorService executor = Executors.newFixedThreadPool(INDEXER_THREAD_POOL_SIZE);
		for (File subdir : subdirs) {
			executor.submit(new IndexerThread(subdir, indexWriter, validDocIds));
		}
		ThreadUtils.shutdownExecutor(executor);

		System.out.println("Closing index...");
		indexWriter.close();

		long end = System.currentTimeMillis();
		System.out.println("\nIndexed " + directory.toPath().normalize() + ", took " + (end - begin) / (1e3 * 60)
				+ " minutes\n\n");
	}

	static class IndexerThread implements Runnable {
		private final File directory;
		private final IndexWriter indexWriter;
		private final List<String> validDocIds;

		public IndexerThread(File directory, IndexWriter indexWriter, List<String> validDocIds) {
			this.directory = directory;
			this.indexWriter = indexWriter;
			this.validDocIds = validDocIds;
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
					if (validDocIds.contains(pmcid)) {
						List<String> lines = FileUtils.readLines(articleFile);
						String title = lines.get(0);
						String text = Joiner.on("").join(lines.subList(1, lines.size()));
						LuceneUtils.index(indexWriter, new Article(pmcid, title, text));
					} else {
						System.out.println("Ignoring invalid or duplicate article " + articleFile.toPath().normalize());
					}
				} catch (Throwable e) {
					e.printStackTrace();
				}
			}

			long end = System.currentTimeMillis();
			System.out.println("\nFinished indexing " + directory.toPath().normalize() + " took "
					+ (end - start) / (1e3 * 60) + " minutes.\n");
		}
	}
}
