package ch.ethz.inf.da.cds.ir.util;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Set;

import org.apache.commons.io.FileUtils;

import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.Multimap;
import com.google.common.collect.Sets;

public class QrelUtils {
	public static Set<String> getQrels(String qrelFile) throws IOException {
		List<String> qrelsLines = FileUtils.readLines(new File(qrelFile));
		Set<String> relevanQrels = Sets.newHashSet();
		for (String qrel : qrelsLines) {
			String[] parts = qrel.split("\\s+");
			String docId = parts[2];
			int relevance = Integer.parseInt(parts[3]);

			if (relevance > 0) {
				relevanQrels.add(docId);
			}
		}

		return relevanQrels;
	}

	public static Multimap<Integer, String> listKnownDocs2014() throws IOException {
		List<String> qrels = FileUtils.readLines(new File("../data/qrels2014.txt"));
		Multimap<Integer, String> knownDocs = ArrayListMultimap.create();
		for (String qrel : qrels) {
			String[] parts = qrel.split("\\s+");
			int topic = Integer.parseInt(parts[0]);
			String docId = parts[2];
			int relevance = Integer.parseInt(parts[3]);

			if (relevance > 0) {
				knownDocs.put(topic, docId);
			}
		}

		int total = 0;
		for (int topic = 1; topic <= 30; topic++) {
			int size = knownDocs.get(topic).size();
			total += size;
			System.out.println(topic + " -> " + size);
		}

		System.out.println(total);

		return knownDocs;
	}

	public static void unkownsResults2015() throws IOException {
		List<String> results = FileUtils.readLines(new File("../data/results-2015-A.txt"));
		Set<String> res2015 = Sets.newHashSet();
		for (String res : results) {
			String[] parts = res.split("\\s+");
			String docId = parts[2];
			int rank = Integer.parseInt(parts[3]);
			if (rank <= 10) {
				res2015.add(docId);
			}
		}
		Set<String> qrels2015 = getQrels("../data/qrels-treceval-2015.txt");
		res2015.removeAll(qrels2015);
		System.out.println(res2015.size());

	}

	public static void main(String[] args) throws IOException {
		// Set<String> qrels2014 = getQrels("../data/qrels2014.txt");
		// Set<String> qrels2015 = getQrels("../data/qrels-treceval-2015.txt");
		// Set<String> all = Sets.newHashSet(qrels2014);
		// all.addAll(qrels2015);
		// System.out.println(all.size());

		Set<String> diags = Sets.newHashSet();
		Set<String> tests = Sets.newHashSet();
		Set<String> treats = Sets.newHashSet();

		int diag = 0, test = 0, treat = 0;
		for (String qrel : FileUtils.readLines(new File("../data/qrels2014.txt"))) {
			String[] parts = qrel.split("\\s+");
			int topic = Integer.parseInt(parts[0]);
			String docId = parts[2];
			int relevance = Integer.parseInt(parts[3]);
			if (topic <= 10) {
				if (relevance > 0) {
					diag++;
					diags.add(docId);
				}
			} else if (topic <= 20) {
				if (relevance > 0) {
					test++;
					tests.add(docId);
				}
			} else {
				if (relevance > 0) {
					treat++;
					treats.add(docId);
				}
			}
		}
		System.out.println(diag + " " + test + " " + treat);
		System.out.println(diags.size() + " " + tests.size() + " " + treats.size());

		diags.retainAll(tests);
		System.out.println(diags);
	}
}
