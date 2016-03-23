package ch.ethz.inf.da.cds.ir.util;

import java.io.File;
import java.io.IOException;
import java.util.List;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.apache.commons.io.FilenameUtils;
import org.w3c.dom.Document;
import org.w3c.dom.NamedNodeMap;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import com.google.common.base.Optional;
import com.google.common.collect.Lists;

import ch.ethz.inf.da.cds.ir.Article;
import ch.ethz.inf.da.cds.ir.Topic;

public class XmlUtils {

	public static Article parseArticle(File file) throws IOException, ParserConfigurationException {
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
		StringBuilder text = new StringBuilder();
		NodeList nodes = doc.getElementsByTagName("p");
		for (int i = 0; i < nodes.getLength(); i++) {
			text.append(nodes.item(i).getTextContent());
			text.append("\n\n");
		}

		return new Article(pmcid, title, text.toString());
	}

	public static List<Topic> parseTopics(File file) throws ParserConfigurationException, SAXException, IOException {
		DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
		DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
		Document doc = dBuilder.parse(file);
		doc.getDocumentElement().normalize();

		List<Topic> topics = Lists.newArrayList();

		NodeList nodes = doc.getElementsByTagName("topic");
		for (int i = 0; i < nodes.getLength(); i++) {
			Node node = nodes.item(i);
			NamedNodeMap attributes = node.getAttributes();
			int id = Integer.parseInt(attributes.getNamedItem("number").getTextContent());
			Topic.TYPE type = Topic.TYPE.valueOf(attributes.getNamedItem("type").getTextContent().toUpperCase());

			NodeList children = node.getChildNodes();
			String description = children.item(1).getTextContent().trim();
			String summary = children.item(3).getTextContent().trim();

			Optional<String> diagnosis = Optional.absent();
			if (children.getLength() > 5) {
				diagnosis = Optional.of(children.item(5).getTextContent().trim());
			}

			topics.add(new Topic(id, type, description, summary, diagnosis));
		}

		return topics;
	}

}
