package ch.ethz.inf.da.cds.ir.convert;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;

import org.apache.commons.io.FilenameUtils;

import com.google.common.collect.Lists;

public class ConverterUtils {
    public static void convert(Path srcRootDir, Path destRootDir, Function<File, Optional<String>> fileCallable)
            throws InterruptedException {
        List<Thread> threads = Lists.newArrayList();
        for (String dir : new String[] { "00", "01", "02", "03" }) {
            Path srcDir = srcRootDir.resolve(dir);
            Path destDir = destRootDir.resolve(dir);
            destDir.toFile().mkdir();
            threads.add(new Thread(() -> convertDirectory(srcDir, destDir, fileCallable)));
        }

        for (Thread thread : threads) {
            thread.start();
        }
        for (Thread thread : threads) {
            thread.join();
        }
    }

    private static void convertDirectory(Path srcDir, Path destDir, Function<File, Optional<String>> fileCallable) {
        System.out.println("\nConverting " + srcDir.normalize() + "\n");
        long begin = System.currentTimeMillis();

        File[] srcSubdirs = srcDir.toFile().listFiles();
        Arrays.sort(srcSubdirs);

        for (File srcSubdir : srcSubdirs) {
            Path destSubdir = destDir.resolve(srcSubdir.getName());
            destSubdir.toFile().mkdir();

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

        double took = (System.currentTimeMillis() - begin) / (1e3 * 60);
        System.out.println("\nConverted " + srcDir.normalize() + ", took " + took + " min.\n");
    }
}
