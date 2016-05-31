package ch.ethz.inf.da.cds.ir.util;

import java.io.File;
import java.io.IOException;
import java.util.List;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.apache.commons.io.FilenameUtils;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NamedNodeMap;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import ch.ethz.inf.da.cds.ir.Article;
import ch.ethz.inf.da.cds.ir.FilePaths;
import ch.ethz.inf.da.cds.ir.TrecQuery;

import com.google.common.base.Optional;
import com.google.common.collect.Lists;

public class XmlUtils {
    public static Article parseArticle(File file) throws Exception {
        DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();

        String pmcid = FilenameUtils.getBaseName(file.getName());

        Document doc;
        try {
            doc = dBuilder.parse(file);
        } catch (SAXException | IOException e) {
            throw new IOException("Error parsing document " + file.getAbsolutePath() + " : " + e.getMessage(),
                                  e);
        }
        doc.getDocumentElement().normalize();

        String title = "";
        NodeList titleNodeList = doc.getElementsByTagName("article-title");
        if (titleNodeList.getLength() > 0) {
            title = titleNodeList.item(0).getTextContent();
        }

        StringBuilder body = new StringBuilder();
        NodeList abstractNodeList = doc.getElementsByTagName("abstract");
        if (abstractNodeList.getLength() > 0) {
            getTextContentRecursive(body, abstractNodeList.item(0));
        }

        body.append("\n\n");

        NodeList bodyNodeList = doc.getElementsByTagName("body");
        if (bodyNodeList.getLength() > 0) {
            getTextContentRecursive(body, bodyNodeList.item(0));
        }

        return new Article(pmcid,
                           title,
                           body.toString());
    }

    private static void getTextContentRecursive(StringBuilder sb, Node node) {
        Node child = node.getFirstChild();
        while (child != null) {
            if (child.getNodeType() == Node.TEXT_NODE) {
                String content = child.getTextContent();
                if (content != null) {
                    sb.append(' ');
                    sb.append(content);
                }
            } else {
                getTextContentRecursive(sb, child);
            }
            child = child.getNextSibling();
        }
    }

    public static List<TrecQuery> parseQueries(File file) throws ParserConfigurationException, SAXException,
            IOException {
        DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
        Document doc = dBuilder.parse(file);
        doc.getDocumentElement().normalize();

        List<TrecQuery> queries = Lists.newArrayList();

        NodeList nodes = doc.getElementsByTagName("topic");
        for (int i = 0; i < nodes.getLength(); i++) {
            Node node = nodes.item(i);
            NamedNodeMap attributes = node.getAttributes();
            int id = Integer.parseInt(attributes.getNamedItem("number").getTextContent());
            TrecQuery.TYPE type = TrecQuery.TYPE.valueOf(attributes.getNamedItem("type")
                                                                   .getTextContent()
                                                                   .toUpperCase());

            NodeList children = node.getChildNodes();
            String description = children.item(1).getTextContent().trim();
            String summary = children.item(3).getTextContent().trim();

            // summary = summary.replaceAll("\\d+", " ");
            // summary = summary.replaceAll("\\byear\\b", " ");
            // summary = summary.replaceAll("\\bold\\b", " ");
            // summary = summary.replaceAll("\\byo\\b", " ");
            // summary = summary.replaceAll("\\bwho\\b", " ");
            // summary = summary.replaceAll("\\bwith\\b", " ");
            // summary = summary.replaceAll("\\bfrom\\b", " ");
            // summary = summary.replaceAll("\\bmale\\b", " ");
            // summary = summary.replaceAll("\\bfemale\\b", " ");
            // summary = summary.replaceAll("\\badult\\b", " ");
            // summary = summary.replaceAll("\\bleft\\b", " ");
            // summary = summary.replaceAll("\\bright\\b", " ");
            // summary = summary.replaceAll("\\bhe\\b", " ");
            // summary = summary.replaceAll("\\bshe\\b", " ");
            // summary = summary.replaceAll("\\bher\\b", " ");
            // summary = summary.replaceAll("\\bwhile\\b", " ");
            // summary = summary.replaceAll("\\bnormal\\b", " ");
            // summary = summary.replaceAll("\\bday\\w*\\b", " ");
            // summary = summary.replaceAll("\\bweek\\w*\\b", " ");
            // summary = summary.replaceAll("\\bmonth\\w*\\b", " ");
            // summary = summary.replaceAll("\\bboth\\b", " ");
            // summary = summary.replaceAll("\\bnow\\b", " ");
            //
            // System.out.println(summary);
            //
            // if (id <= 10) {
            // summary += " diagnosis diagnose";
            // }
            // if (id > 10 && id <= 20) {
            // summary += " routine test";
            // }
            // if (id > 20) {
            // summary += " therapy treat treatment";
            // }

            Optional<String> diagnosis = Optional.absent();
            if (children.getLength() > 5) {
                diagnosis = Optional.of(children.item(5).getTextContent().trim());
            }

            queries.add(new TrecQuery(id,
                                      type,
                                      description,
                                      summary,
                                      diagnosis));
        }

        return queries;
    }

    private static void writeQueriesTerrierFormat(List<TrecQuery> queries, File outFile) throws Exception {
        DocumentBuilderFactory docFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder docBuilder = docFactory.newDocumentBuilder();

        Document doc = docBuilder.newDocument();
        Element rootElement = doc.createElement("topics");
        doc.appendChild(rootElement);

        for (TrecQuery query : queries) {
            Element queryElement = doc.createElement("topic");
            rootElement.appendChild(queryElement);

            Element numberElement = doc.createElement("number");
            numberElement.setTextContent(Integer.toString(query.getId()));
            queryElement.appendChild(numberElement);

            Element summaryElement = doc.createElement("summary");
            summaryElement.setTextContent(query.getSummary());
            queryElement.appendChild(summaryElement);
        }

        TransformerFactory transformerFactory = TransformerFactory.newInstance();
        Transformer transformer = transformerFactory.newTransformer();
        transformer.setOutputProperty(OutputKeys.INDENT, "yes");
        transformer.setOutputProperty("{http://xml.apache.org/xslt}indent-amount", "4");

        DOMSource source = new DOMSource(doc);
        StreamResult result = new StreamResult(outFile);

        transformer.transform(source, result);
    }

    public static void main(String[] args) throws Exception {
        // System.out.println(parseArticle(new
        // File(FilePaths.PMC_00_DIR.toString() + "/00/2637234.nxml")));

        List<TrecQuery> queries2014 = parseQueries(FilePaths.QUERIES_2014_FILE.toFile());
        writeQueriesTerrierFormat(queries2014, FilePaths.QUERIES_DIR.resolve("topics-2014-terrier.xml")
                                                                    .toFile());

        List<TrecQuery> queries2015 = parseQueries(FilePaths.QUERIES_2015_A_FILE.toFile());
        writeQueriesTerrierFormat(queries2015, FilePaths.QUERIES_DIR.resolve("topics-2015-terrier.xml")
                                                                    .toFile());
    }
}
