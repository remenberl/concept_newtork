# -*- coding: UTF-8 -*-
#### this script finds related wiki pages from wikification results of Tagme
import MySQLdb as mdb
import json
import networkx as nx
import xml.etree.ElementTree as ET
import mwparserfromhell

database_url = '127.0.0.1'

threshold = 0.35    # threshold to filter unqualified Wikification results
out_file = "results/wikification_brief_results.txt"
out2_file = "results/wiki_page_rank.txt"
redirect_file = "results/wiki_redirection.txt"
wikipedia_file = 'enwiki-20110115-pages-articles.xml' # path to wiki dump

# First stage, transform wikification results
con = mdb.connect(host=database_url, port=1720, user='root', passwd='admin', db='wiki_ontology', charset='utf8');
cursor = con.cursor()
cursor.execute("SELECT * FROM dblp_wikification")
rows = cursor.fetchall()

i = 0
with open(out_file, 'w') as output: 
    for row in rows:
        try:
            id = int(row[0])
            abstract = row[5]
            tagme_result = json.loads(row[6])
            annotations = tagme_result["annotations"]
            for annotation in annotations:
                title = annotation["title"]
                start = annotation["start"]
                end = annotation["end"]
                rho = float(annotation["rho"])
                if rho < threshold:
                    continue
                output.write(str(id) + '\t' + title.encode('utf-8') + '\t' + str(rho) + '\n')
            i += 1
            if i != 0 and i % 1000 == 0:
                print "Finish scanning " + str(i) + " papers."
        except Exception:
            print "error"
            continue

# Second stage, aggregate mentions for wiki entries appeared in the corpus
wiki_entry_score_dict = dict()
with open(out_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        rho = float(elements[-1])
        if rho > threshold:
            wiki_entry = elements[-2].strip().lower()
            wiki_entry_score_dict.setdefault(wiki_entry, 0)
            wiki_entry_score_dict[wiki_entry] += 1

# Third stage, run pagerank on wiki network
def transform_string(s):
    s=s.replace("\xE2\x80\x89"," ")
    s=s.replace("\xE2\x80\x93","-")
    s=s.replace("\xE2\x80\x94","-")
    s=s.replace("\xE2\x80\x98","'")
    s=s.replace("\xE2\x80\x99","'")
    s=s.replace("\xE2\x80\x9C","\"")
    s=s.replace("\xE2\x80\x9D","\"")
    return s


interested_wiki_entries = set()
threshold = 3
for (wiki_entry, freq) in wiki_entry_score_dict.iteritems():
    if freq >= threshold:
        interested_wiki_entries.add(transform_string(wiki_entry))

def find_linked_wiki_entries(wiki_body):
    entries = set()
    wikicode = mwparserfromhell.parse(wiki_body)
    links =  wikicode.filter_wikilinks()
    for link in links:
        title = str(link.title)
        index = title.find('#')
        if index > 0:
            title = title[:index]
        elif index == 0:
            continue
        try:
            entries.add(title.strip().lower().decode('utf-8'))
        except Exception:
            print "find wiki entries error"
            continue
    return entries

redirect_dict = dict()
iterparse = ET.iterparse(wikipedia_file)
i = 0
for event, elem in iterparse:
    if elem.tag.endswith("title"):
        title = elem.text.strip().lower()
    if elem.tag.endswith("text"):
        if title not in interested_wiki_entries:
            title = transform_string(title.encode('utf-8')).decode('utf-8')
            if title not in interested_wiki_entries:
                elem.clear()
                continue
        wiki_body = elem.text
        if wiki_body.find("#REDIRECT") == 0:
            wiki_entries = find_linked_wiki_entries(wiki_body)
            redirect_entry = wiki_entries.pop()
            if title == redirect_entry:
                elem.clear()
                continue
            redirect_dict[title] = redirect_entry
            interested_wiki_entries.remove(title)
            interested_wiki_entries.add(redirect_dict[title])
            print title + ': ' + redirect_dict[title]
            i += 1
            if i != 0 and i % 100 == 0:
                print "Finish scanning " + str(i) + " redirect wiki pages."
    elem.clear()

try:
    with open(redirect_file, 'w') as output:
        for (entry1, entry2) in redirect_dict.iteritems():
            output.write(entry1.encode('utf-8') + '\t' + entry2.encode('utf-8') +  '\n')
except Exception:
    pass
try:
    with open(redirect_file, 'r') as input:
        for line in input:
            elements = line.split('\t')
            redirect_dict[elements[0].strip()] = elements[1].strip()
            interested_wiki_entries.remove(elements[0].strip())
            interested_wiki_entries.add(elements[1].strip())
except Exception:
    pass

iterparse = ET.iterparse(wikipedia_file)
G = nx.DiGraph()
i = 0
for event, elem in iterparse:
    if elem.tag.endswith("title"):
        title = elem.text.strip().lower()
    if elem.tag.endswith("text"):
        if title not in interested_wiki_entries:
            title = transform_string(title.encode('utf-8')).decode('utf-8')
            if title not in interested_wiki_entries:
                elem.clear()
                continue
        wiki_body = elem.text
        wiki_entries = find_linked_wiki_entries(wiki_body)
        for wiki_entry in wiki_entries:
            if wiki_entry != title:
                if wiki_entry in interested_wiki_entries:
                    G.add_edge(wiki_entry, title)
                elif transform_string(wiki_entry.encode('utf-8')) in interested_wiki_entries:
                    G.add_edge(transform_string(wiki_entry.encode('utf-8')), title)
                elif wiki_entry in redirect_dict:
                    G.add_edge(redirect_dict[wiki_entry], title)
        i += 1
        if i != 0 and i % 100 == 0:
            print "Finish scanning " + str(i) + " wiki pages."
    elem.clear()

G_ = G.to_undirected()
nodes_degree = dict()
nodes_indegree = dict()
nodes_outdegree = dict()
for node in G.nodes():
    nodes_degree[node] = G.degree(node)
    nodes_indegree[node] = G.in_degree(node)
    nodes_outdegree[node] = G.out_degree(node)

print len(G_.nodes())
print "Start PageRank"
personalization = {}
# Wiki entries with top score in tems of counts appear in personalization vector
for (wiki_entry, freq) in wiki_entry_score_dict.iteritems():
    if freq >= 100:
        personalization[wiki_entry.decode("utf-8")] = 1

for node in G_.nodes():
    if node not in personalization:
        personalization[node] = 0

pr = nx.pagerank_scipy(G_, alpha=0.6, personalization=personalization)
for (i, j) in pr.items():
    if i in wiki_entry_score_dict:
        pr[i] += wiki_entry_score_dict[i] * 0.00000001
pr = sorted(pr.items(), key=lambda x:-x[1])
with open(out2_file, 'w') as output:
    for i in pr:
        try:
            if wiki_entry_score_dict[i[0]] > 2:
                try:
                    output.write(i[0].encode('utf-8') + '\t' + str(i[1]) + '\t' + str(wiki_entry_score_dict[i[0]]) + '\t' + str(i[0] in G_.nodes()) + '\n')
                except:
                    output.write(i[0].decode('utf-8') + '\t' + str(i[1]) + '\t' + str(wiki_entry_score_dict[i[0]]) + '\t' + str(i[0] in G_.nodes()) + '\n')
        except Exception:
            continue