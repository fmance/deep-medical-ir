package ch.ethz.inf.da.cds.ir.util;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.tuple.Pair;

import com.google.common.collect.Maps;

public class QrelUtils {
    public static Map<Pair<Integer, Integer>, Integer> getRelevance(Path qrels) throws IOException {
        Map<Pair<Integer, Integer>, Integer> relevances = Maps.newHashMap();

        for (String line : FileUtils.readLines(qrels.toFile())) {
            String[] parts = line.split("\\s+");
            int queryId = Integer.parseInt(parts[0]);
            int docId = Integer.parseInt(parts[2]);
            int relevance = Integer.parseInt(parts[3]);
            relevances.put(Pair.of(queryId, docId), relevance);
        }

        return relevances;
    }

    public static Map<Integer, Integer> getRelevance(Path qrels, int queryId) throws IOException {
        Map<Integer, Integer> relevances = Maps.newHashMap();
        for (String line : FileUtils.readLines(qrels.toFile())) {
            String[] parts = line.split("\\s+");
            if (Integer.parseInt(parts[0]) == queryId) {
                int docId = Integer.parseInt(parts[2]);
                int relevance = Integer.parseInt(parts[3]);
                relevances.put(docId, relevance);
            }

        }
        return relevances;
    }
}
