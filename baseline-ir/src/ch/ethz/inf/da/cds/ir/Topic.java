package ch.ethz.inf.da.cds.ir;

import com.google.common.base.Optional;

public class Topic {
	public static enum TYPE {
		DIAGNOSIS, TEST, TREATMENT
	}

	private final int id;
	private final TYPE type;
	private final String description;
	private final String summary;
	private final Optional<String> diagnosis;

	public Topic(int id, TYPE type, String description, String summary, Optional<String> diagnosis) {
		this.id = id;
		this.type = type;
		this.description = description;
		this.summary = summary;
		this.diagnosis = diagnosis;
	}

	public int getId() {
		return id;
	}

	public TYPE getType() {
		return type;
	}

	public String getDescription() {
		return description;
	}

	public String getSummary() {
		return summary;
	}

	public Optional<String> getDiagnosis() {
		return diagnosis;
	}

	@Override
	public String toString() {
		return "Topic [id=" + id + ", type=" + type + ", description=" + description + ", summary=" + summary
				+ ", diagnosis=" + diagnosis + "]";
	}

}
