package ch.ethz.inf.da.cds.ir.convert;

import java.io.File;
import java.io.PrintWriter;
import java.util.List;
import java.util.Optional;

import org.apache.commons.io.FilenameUtils;

import ch.ethz.inf.da.cds.ir.Article;
import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.TrecQuery;
import ch.ethz.inf.da.cds.ir.util.DocUtils;
import ch.ethz.inf.da.cds.ir.util.XmlUtils;

/**
 * Convert the XML files in the PMC directories into plaintext files.
 * 
 * @author fmance
 *
 */
public class XmlToPlaintextConverter {
    private static final List<String> VALID_DOC_IDS = DocUtils.getValidDocIds();

    public static void main(String[] args) throws Exception {
        FilePaths.PLAINTEXT_DIR.toFile().mkdir();
        ConverterUtils.convert(FilePaths.XML_DIR, FilePaths.PLAINTEXT_DIR, XmlToPlaintextConverter::getTextContent);
    }

    private static Optional<String> getTextContent(File xmlFile) {
        if (!xmlFile.getName().endsWith(".nxml")) {
            return Optional.empty();
        }

        String pmcid = FilenameUtils.getBaseName(xmlFile.getName());
        if (!VALID_DOC_IDS.contains(pmcid)) {
            return Optional.empty();
        }

        try {
            Article article = XmlUtils.parseArticle(xmlFile);
            return Optional.of(article.getTitle() + ".\n\n" + article.getText());
        } catch (Throwable e) {
            e.printStackTrace();
            return Optional.empty();
        }
    }

    private static void convertQuerySummaries(File xmlQueryFile, File plaintextQueryFile) throws Exception {
        List<TrecQuery> queries = XmlUtils.parseQueries(xmlQueryFile);
        PrintWriter pw = new PrintWriter(plaintextQueryFile);
        for (TrecQuery query : queries) {
            pw.printf("%d %s\n", query.getId(), query.getSummary());
        }
        pw.close();
    }
}
