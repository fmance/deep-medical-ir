package ch.ethz.inf.da.cds.ir.convert;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Optional;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Function;

import org.apache.commons.io.FilenameUtils;

import ch.ethz.inf.da.cds.ir.util.ThreadUtils;

public class ConverterUtils {
    public static void convert(Path srcRootDir, Path destRootDir, Function<File, Optional<String>> fileCallable)
            throws InterruptedException {
        for (String dir : new String[] { "00", "01", "02", "03" }) {
            Path srcDir = srcRootDir.resolve(dir);
            Path destDir = destRootDir.resolve(dir);
            destDir.toFile().mkdir();
            convertDirectory(srcDir, destDir, fileCallable);
        }
    }

    private static void convertDirectory(Path srcDir, Path destDir, Function<File, Optional<String>> fileCallable) {
        System.out.println("\nConverting " + srcDir.normalize() + "\n");
        long begin = System.currentTimeMillis();

        File[] srcSubdirs = srcDir.toFile().listFiles();
        Arrays.sort(srcSubdirs);

        ExecutorService executor = Executors.newFixedThreadPool(4);

        for (File srcSubdir : srcSubdirs) {
            Path destSubdir = destDir.resolve(srcSubdir.getName());
            destSubdir.toFile().mkdir();
            executor.submit(new ConverterThread(srcSubdir, destSubdir, fileCallable));

        }
        ThreadUtils.shutdownExecutor(executor);

        double took = (System.currentTimeMillis() - begin) / (1e3 * 60);
        System.out.println("\nConverted " + srcDir.normalize() + ", took " + took + " min.\n");
    }

    static class ConverterThread implements Runnable {
        private final File srcSubdir;
        private final Path destSubdir;
        private final Function<File, Optional<String>> fileCallable;

        public ConverterThread(File srcSubdir, Path destSubdir, Function<File, Optional<String>> fileCallable) {
            this.srcSubdir = srcSubdir;
            this.destSubdir = destSubdir;
            this.fileCallable = fileCallable;
        }

        @Override
        public void run() {
            Path srcSubdirPath = srcSubdir.toPath().normalize();
            System.out.println("Converting " + srcSubdirPath + " to " + destSubdir.toAbsolutePath());
            long start = System.currentTimeMillis();

            int filesWritten = 0;
            for (File file : srcSubdir.listFiles()) {
                Optional<String> result = fileCallable.apply(file);
                if (!result.isPresent()) {
                    continue;
                }

                String pmcid = FilenameUtils.getBaseName(file.getName());
                File outFile = destSubdir.resolve(pmcid + ".txt").toFile();
                try {
                    PrintWriter pw = new PrintWriter(outFile);
                    pw.println(result.get());
                    pw.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
                filesWritten++;

                if (filesWritten % 500 == 0) {
                    double took = (System.currentTimeMillis() - start) / 1e3;
                    System.out.println("Dir " + srcSubdirPath + ": " + filesWritten + " files in " + took + " sec.");
                }
            }

            double took = (System.currentTimeMillis() - start) / (1e3 * 60);
            System.out.println("Finished " + srcSubdirPath + " " + filesWritten + " files in " + took + " min.");
        }

    }

}
