package ch.ethz.inf.da.cds.ir;

import com.google.common.base.Optional;

public class TrecQuery {
    public static enum TYPE {
        DIAGNOSIS, TEST, TREATMENT
    }

    private final int id;
    private final TYPE type;
    private final String note;
    private final String description;
    private final String summary;
    private final Optional<String> diagnosis;

    public TrecQuery(int id, TYPE type, String description, String summary, String note, Optional<String> diagnosis) {
        this.id = id;
        this.type = type;
        this.description = description;
        this.summary = summary;
        this.note = note;
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

    public String getNote() {
        return note;
    }

    public Optional<String> getDiagnosis() {
        return diagnosis;
    }

    @Override
    public String toString() {
        return "TrecQuery [id=" + id + ",\ntype=" + type + ",\nnote=" + note + ",\ndescription=" + description
               + ",\nsummary=" + summary + ",\ndiagnosis=" + diagnosis + "]\n";
    }

}
