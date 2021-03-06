package uk.ac.shef.dcs.oak.jate.io;

import uk.ac.shef.dcs.oak.jate.JATEException;
import uk.ac.shef.dcs.oak.jate.core.feature.indexer.GlobalIndex;
import uk.ac.shef.dcs.oak.jate.model.Document;
import uk.ac.shef.dcs.oak.jate.model.Term;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Set;

/**
 * A helper class which outputs term recognition results
 *
 * @author <a href="mailto:z.zhang@dcs.shef.ac.uk">Ziqi Zhang</a>
 */


public class ResultWriter2File {

	private GlobalIndex _index;

	/**
	 * @param index an instance of GlobalIndexMem. The writer will read mapping data from term canonical from to variant
	 * forms and output the result
	 */
	public ResultWriter2File(GlobalIndex index) {
		this._index = index;
	}

	/**
	 * Output the result. This writes one term on a line in the format of:
	 * <p>
	 * canonical |variant1 |variant2 |variantX       confidence
	 * </p>
	 * @param result term recognition result sorted descendingly by confidence
	 * @param path output file path
	 * @throws uk.ac.shef.dcs.oak.jate.JATEException
	 */
	public void output(Term[] result, String path) throws JATEException {
		try {
			PrintWriter pw = new PrintWriter(new FileWriter(path));
			if (_index == null) {
				for (Term c : result) {
					pw.println(c.getConcept() + "\t\t\t" + c.getConfidence());
				}
			}
			else{
				for (Term c : result) {
					Set<String> originals = _index.retrieveVariantsOfTermCanonical(c.getConcept());
					Set<Document> docs = _index.retrieveDocsContainingTermCanonical(c.getConcept());
					if(originals==null)
						pw.println(c.getConcept() + "\t\t\t" + c.getConfidence());
					else
						pw.println(c.getConcept()+" |"+writeToString(originals) + "\t\t\t" + c.getConfidence());
						pw.println("#"+writeToStringFromDocs(docs));
				}
			}
			pw.close();
		}
		catch (IOException ioe) {
			throw new JATEException(ioe);
		}
	}

	private String writeToString(Set<String> container){
		StringBuilder sb = new StringBuilder();
		for(String s:container){
			sb.append(s).append(" |");
		}
		return sb.toString().substring(0,sb.lastIndexOf("|"));
	}
	private String writeToStringFromDocs(Set<Document> docs){
		StringBuilder sb = new StringBuilder();
		for(Document d:docs){
			String s = d.getUrl().getFile();
			s = s.substring(s.lastIndexOf('/') + 1);
			sb.append(s).append(" #");
		}
		return sb.toString().substring(0,sb.lastIndexOf("#"));
	}
}
