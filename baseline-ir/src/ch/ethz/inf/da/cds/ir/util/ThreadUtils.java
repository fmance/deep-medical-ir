package ch.ethz.inf.da.cds.ir.util;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;

public class ThreadUtils {
	public static void shutdownExecutor(ExecutorService executor) {
		executor.shutdown();
		try {
			// Wait a while for existing tasks to terminate
			if (!executor.awaitTermination(1, TimeUnit.DAYS)) {
				executor.shutdownNow(); // Cancel currently executing tasks
				// Wait a while for tasks to respond to being cancelled
				if (!executor.awaitTermination(1, TimeUnit.DAYS))
					System.err.println("Pool did not terminate");
			}
		} catch (InterruptedException ie) {
			// (Re-)Cancel if current thread also interrupted
			executor.shutdownNow();
			// Preserve interrupt status
			Thread.currentThread().interrupt();
		}
	}

}
