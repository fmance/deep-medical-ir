package ch.ethz.inf.da.cds.ir.util;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;
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
import org.apache.lucene.analysis.en.EnglishAnalyzer;
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
import com.sun.org.apache.xerces.internal.dom.TextImpl;

public class XmlUtils {
    public static Article parseArticle(File file) throws Exception {
        DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();

        String pmcid = FilenameUtils.getBaseName(file.getName());

        Document doc;
        try {
            doc = dBuilder.parse(file);
        } catch (SAXException | IOException e) {
            throw new IOException("Error parsing document " + file.getAbsolutePath() + " : " + e.getMessage(), e);
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
            getTextContent(body, abstractNodeList.item(0));
        }

        body.append("\n\n");

        NodeList bodyNodeList = doc.getElementsByTagName("body");
        if (bodyNodeList.getLength() > 0) {
            getTextContent(body, bodyNodeList.item(0));
        }

        return new Article(pmcid, title, body.toString());
    }

    private static void getTextContent(StringBuilder sb, Node node) {
        Node child = node.getFirstChild();
        if (child != null) {
            Node next = child.getNextSibling();
            if (next == null) {
                if (hasTextContent(child)) {
                    sb.append(' ');
                    sb.append((child).getTextContent());
                }
            }
            getTextContentRecursive(sb, node);
        }
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

    private static boolean hasTextContent(Node child) {
        return child.getNodeType() != Node.COMMENT_NODE && child.getNodeType() != Node.PROCESSING_INSTRUCTION_NODE
               && (child.getNodeType() != Node.TEXT_NODE || ((TextImpl) child).isIgnorableWhitespace() == false);
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
            TrecQuery.TYPE type = TrecQuery.TYPE.valueOf(attributes.getNamedItem("type").getTextContent().toUpperCase());

            NodeList children = node.getChildNodes();
            String description = children.item(1).getTextContent().trim();
            String summary = children.item(3).getTextContent().trim();

            Optional<String> diagnosis = Optional.absent();
            if (children.getLength() > 5) {
                diagnosis = Optional.of(children.item(5).getTextContent().trim());
            }

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

            queries.add(new TrecQuery(id, type, description, summary, diagnosis));
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

    private static void convertPubmedXmlToArticleLines() throws FileNotFoundException, Exception {
        Path hedgesDataDir = FilePaths.ROOT_DIR.resolve("classification/data/hedges");
        PrintWriter pw = new PrintWriter(hedgesDataDir.resolve("results-analyzed.txt").toFile());
        PrintWriter idpw = new PrintWriter(hedgesDataDir.resolve("results-analyzed-ids.txt").toFile());

        parsePubmedXml(hedgesDataDir.resolve("results00.xml").toFile(), pw, idpw);
        parsePubmedXml(hedgesDataDir.resolve("results01.xml").toFile(), pw, idpw);
        parsePubmedXml(hedgesDataDir.resolve("results02.xml").toFile(), pw, idpw);
        parsePubmedXml(hedgesDataDir.resolve("results03.xml").toFile(), pw, idpw);

        pw.close();
        idpw.close();
    }

    private static void parsePubmedXml(File file, PrintWriter out, PrintWriter idout) throws Exception {
        DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();

        Document doc = dBuilder.parse(file);
        doc.getDocumentElement().normalize();

        List<String> pmids = Lists.newArrayList();
        NodeList pubmedNodes = doc.getElementsByTagName("PubmedArticle");
        for (int i = 0; i < pubmedNodes.getLength(); i++) {
            pmids.add(pubmedNodes.item(i).getChildNodes().item(1).getChildNodes().item(1).getTextContent());
        }

        List<String> titles = Lists.newArrayList();
        NodeList titleNodes = doc.getElementsByTagName("ArticleTitle");
        for (int i = 0; i < titleNodes.getLength(); i++) {
            titles.add(titleNodes.item(i).getTextContent());
        }

        List<String> texts = Lists.newArrayList();
        NodeList articleNodes = doc.getElementsByTagName("Article");
        for (int i = 0; i < articleNodes.getLength(); i++) {
            Element article = (Element) articleNodes.item(i);
            NodeList textNode = article.getElementsByTagName("Abstract");
            if (textNode.getLength() > 0) {
                texts.add(textNode.item(0).getTextContent());
            } else {
                texts.add("EMPTY");
            }
        }

        assert pmids.size() == titles.size();
        assert pmids.size() == texts.size();

        for (int i = 0; i < pmids.size(); i++) {
            String pmid = pmids.get(i);
            idout.println(pmid);

            String text = titles.get(i) + texts.get(i);
            text = text.replaceAll("\\P{L}", " ");
            List<String> tokens = LuceneUtils.tokenizeString(new EnglishAnalyzer(), text);
            text = String.join(" ", tokens);
            out.println(text);
        }
    }

    public static void main(String[] args) throws Exception {
        convertPubmedXmlToArticleLines();

        // System.out.println(parseArticle(FilePaths.XML_DIR.resolve("01/00/3123283.nxml").toFile()));
        // List<TrecQuery> queries2014 =
        // parseQueries(FilePaths.QUERIES_2014_FILE.toFile());
        // writeQueriesTerrierFormat(queries2014,
        // FilePaths.QUERIES_DIR.resolve("topics-2014-terrier.xml").toFile());
        //
        // List<TrecQuery> queries2015 =
        // parseQueries(FilePaths.QUERIES_2015_A_FILE.toFile());
        // writeQueriesTerrierFormat(queries2015,
        // FilePaths.QUERIES_DIR.resolve("topics-2015-terrier.xml").toFile());
    }

}
