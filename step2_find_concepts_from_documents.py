# -*- coding: UTF-8 -*-
#### this script prepares text for extracting concepts from both Wiki pages and documents based on Jate
import MySQLdb as mdb
import xml.etree.ElementTree as ET 
import mwparserfromhell
import os
import base64
import re

database_url = '127.0.0.1'
threshold = 5.8e-05 # threhold for pagerank score
wiki_dblp_documents_folder = "results/wiki_dblp_documents/" # folder for keeping large amounts of files related to Wiki entries and paper abstracts
interested_wiki_entries_file = "results/wiki_page_rank.txt" # results generated in step 1
wikipedia_file = 'enwiki-20110115-pages-articles.xml'   # wiki dump
concpets_folder = "results/"   # using

def extract_plain_text(wiki_body):
    wikicode = mwparserfromhell.parse(wiki_body)
    plain_text = ""
    for node in wikicode.nodes:
        type_of_node = type(node)
        if type_of_node == mwparserfromhell.nodes.template.Template:
            continue
        if type_of_node == mwparserfromhell.nodes.argument.Argument:
            continue
        if type_of_node == mwparserfromhell.nodes.comment.Comment:
            continue
        if type_of_node == mwparserfromhell.nodes.html_entity.HTMLEntity:
            continue
        if type_of_node != mwparserfromhell.nodes.text.Text:
            if type(node) == mwparserfromhell.nodes.tag.Tag:
                str_node = node.contents
            elif type(node) == mwparserfromhell.nodes.external_link.ExternalLink:
                str_node = node.title
            elif type(node) == mwparserfromhell.nodes.heading.Heading:
                str_node = node.title
            elif type(node) == mwparserfromhell.nodes.wikilink.Wikilink:
                str_node = node.title
            plain_text += extract_plain_text(str_node)
        else:
            plain_text += str(node)
    return re.sub(r'\([^)]*\)', '', plain_text)

con = mdb.connect(host=database_url, port=1720, user='root', passwd='admin', db='wiki_ontology', charset='utf8');
cursor = con.cursor()
cursor.execute("SELECT id, abstract FROM dblp_wikification")
rows = cursor.fetchall()
_cursor = con.cursor()

# handle document archive
i = 0
for row in rows:
    id = int(row[0])
    document_path = wiki_dblp_documents_folder + str(id)
    if not os.path.exists(document_path):
        abstract = re.sub(r'\([^)]*\)', '', row[1])
        with open(document_path, 'w') as input:
            input.write(abstract.encode("utf8"))
        i += 1
    if i != 0 and i % 100 == 0:
        print "Finish scanning " + str(i) + " papers."

# handle Wikipedia
i = 0
interested_wiki_entries = set()
with open(interested_wiki_entries_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        if float(elements[1]) >= threshold:
            interested_wiki_entries.add(elements[0].strip().lower())
print len(interested_wiki_entries)
def transform_string(s):
    s=s.replace("\xE2\x80\x89"," ")
    s=s.replace("\xE2\x80\x93","-")
    s=s.replace("\xE2\x80\x94","-")
    s=s.replace("\xE2\x80\x98","'")
    s=s.replace("\xE2\x80\x99","'")
    s=s.replace("\xE2\x80\x9C","\"")
    s=s.replace("\xE2\x80\x9D","\"")
    return s


iterparse = ET.iterparse(wikipedia_file)
for event, elem in iterparse:
    try:
        if elem.tag.endswith("title"):
            title = elem.text.strip().lower()
        if elem.tag.endswith("text"):
            if title not in interested_wiki_entries:
                title = transform_string(title.encode('utf-8')).decode('utf-8')
                if title not in interested_wiki_entries:
                    elem.clear()
                    continue
            document_path = wiki_dblp_documents_folder + base64.urlsafe_b64encode(title)
            if not os.path.exists(document_path):
                wiki_body = elem.text
                if wiki_body.find("#REDIRECT") == 0:
                    elem.clear()
                    continue
                wiki_plain_text = extract_plain_text(wiki_body)
                with open(document_path, 'w') as input:
                    input.write(wiki_plain_text)
                i += 1
                if i != 0 and i % 100 == 0:
                    print "Finish scanning " + str(i) + " wiki pages."
    except Exception:
        print "error"
        continue
    elem.clear()

# run code in terminal under folder jate
# java -classpath libs/apache-log4j-1.2.15/log4j-1.2.15.jar:libs/dragon/dragontool.jar:dist/jate.jar:libs/wit-commons/wit-commons.jar:libs/apache-opennlp-1.53/opennlp-tools-1.5.3.jar uk.ac.shef.dcs.oak.jate.test.TestCValue ./results/wiki_dblp_documents/ ./results/


