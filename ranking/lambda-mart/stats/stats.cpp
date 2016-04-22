#include<iostream>
#include<vector>
#include<cmath>
#include<fstream>
#include<unordered_map>
#include<map>
#include<string>
#include<sstream>
#include<set>
#include<iterator>
#include<utility>
#include<algorithm>

using namespace std;

typedef map<int, vector<string>> termsDict_t;
typedef unordered_map<int, unordered_map<string, int>> tf_t;

int numDocs;
double avgDocLen;
unordered_map<string, int> docFreq;
tf_t termFreq;


termsDict_t readTermsDict(string filename) {
    termsDict_t termsDict;
    ifstream in(filename);
    
    string line;
    while (getline(in, line)) {
        istringstream s(line);
        int id;
        string term;
        vector<string> terms;
        
        s >> id;
        while (s >> term) {
            terms.push_back(term);
        }
        termsDict[id] = terms;
    }
    
    in.close();
    return termsDict;
}

double bm25(vector<string> qterms, unordered_map<string, int> docTfs, int docLen) {
    double k1 = 1.2;
    double b = 0.75;
    double score = 0.0;
    for (string &qterm: qterms) {
        double tf = docTfs[qterm];
        double df = docFreq[qterm];
        double idf = log(1 + (numDocs - df + 0.5)/(df + 0.5));
        double norm = k1 * (1.0 - b + b * ((float)docLen)/avgDocLen);
        score += idf * tf * (k1 + 1) / (tf + norm);
    }
    return score;
}



void generateFeatures(termsDict_t queryTermsDict, string outFile) {
    ofstream out(outFile);
    
    for (auto it = queryTermsDict.begin(); it != queryTermsDict.end(); it++) {
        int qid = it->first;
        vector<string> qterms = it->second;
        cout << "query " << qid << endl;

        int counter = 0;
        for (auto termFreqIt = termFreq.begin(); termFreqIt != termFreq.end(); termFreqIt++) {
            int did = termFreqIt->first;
            unordered_map<string, int> docTfs = termFreqIt->second;
            int docLen = 0;
            for (auto tfIt = docTfs.begin(); tfIt != docTfs.end(); tfIt++) {
                docLen += tfIt->second;
            }
            
            double feature_bm25 = bm25(qterms, docTfs, docLen);
            
            out << qid << " " << did << " " << feature_bm25 << endl;
            
            counter++;
            if (counter % 10000 == 0) {
                cout << counter << endl;
            }
        }
        
    }
    
    out.close();
}

void readTermFreq() {
    ifstream in("doc-terms.txt");
    string line;
    int counter = 0;
    while (getline(in, line)) {
        istringstream s(line);
        int did;
        string term;
        vector<string> terms;
        
        s >> did;
        
        unordered_map<string, int> tf;
        while (s >> term) {
            tf[term]++;     
        }
        
        termFreq[did] = tf;
        
        counter++;
        if (counter % 10000 == 0) {
                cout << counter << endl;
        }
    }
    
    in.close();
}

int main() {
    // Read collection stats
    ifstream stats("stats.txt");
    stats >> numDocs >> avgDocLen;
    string term;
    while (stats >> term) {
        int freq;
        stats >> freq;
        docFreq[term] = freq;
    }
    stats.close();
    
    auto query2014TermsDict = readTermsDict("query-2014-terms.txt");
    auto query2015TermsDict = readTermsDict("query-2015-terms.txt");
    
    readTermFreq();
    
    generateFeatures(query2014TermsDict, "features-2014-cpp.txt");

                
    

}
