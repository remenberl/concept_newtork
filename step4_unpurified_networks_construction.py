# -*- coding: UTF-8 -*-
#### this script builds the unpurified networks based on concepts extracted from wiki and document corpus

import base64
import MySQLdb as mdb
import mwparserfromhell
import string
import re
import xml.etree.ElementTree as ET 

server_url = '127.0.0.1'

concepts_list_file = './results/CValue_ALGORITHM.txt'
corpus_network_file = './results/corpus_network.txt'
wikipedia_file = 'enwiki-20110115-pages-articles.xml'

wiki_network_file = './results/wiki_network.txt'
concepts_id_map_file = './results/concepts_id.txt'
interested_wiki_concepts_file = "./results/wiki_page_rank.txt"
stop_words_file = "./results/stopwords.txt"

wiki_concept_pool = dict()
corpus_concept_pool = dict()
concepts_set = set()
surface_form_dict = dict()
concept_dict = dict()
concept_weight_dict = dict()

stopwords = set()
with open(stop_words_file, 'r') as input:
    for line in input:
        stopwords.add(line.strip())

def clean_concept(concept):
    elements = concept.split(' ')
    if len(elements) > 2 and elements[-1] in stopwords:
        return ' '.join(elements[:-1])
    else:
        return concept

with open(concepts_list_file, 'r') as input:
    concept = ""
    for line in input:
        if line[0] != '#':
            elements = line.split('\t')
            if float(elements[-1]) <= 0:
                break
            phrases = elements[0].split('|')
            concept = clean_concept(phrases[0].strip().lower())
            surface_forms = set()
            for phrase in phrases[1:]:
                if phrase.strip().lower() != "":
                    surface_forms.add(phrase.strip().lower())
            for surface_form in surface_forms:
                surface_form_dict[surface_form] = concept
                concept_dict.setdefault(concept, set())
                concept_dict[concept].add(surface_form)
            concepts_set.add(concept)
        else:
            elements = line.split('#')
            for element in elements:
                document_id = element.strip()
                if document_id != "":
                    if document_id.isdigit():
                        corpus_concept_pool.setdefault(document_id, set())
                        corpus_concept_pool[document_id].add(concept)
                        concept_weight_dict.setdefault(concept, [0, 0])
                        concept_weight_dict[concept][0] += 1
                    else:
                        try:
                            wiki_title = base64.urlsafe_b64decode(document_id)
                        except Exception:
                            continue
                        wiki_concept_pool.setdefault(wiki_title, set())
                        wiki_concept_pool[wiki_title].add(concept)
                        concept_weight_dict.setdefault(concept, [0, 0])
                        concept_weight_dict[concept][1] += 1
print "Finish reading in concept-doc relationship."



to_remove_list = list()
for (concept, weights) in concept_weight_dict.iteritems():
    if weights[0] + weights[1] < 5 or weights[0] <= 2:
        to_remove_list.append(concept)
print "In total, there are " + str(len(concept_weight_dict)) + " concepts."
print "Pruning " + str(len(to_remove_list)) + " concepts."

for concept in to_remove_list:
    del concept_weight_dict[concept]

wiki_network = dict()
corpus_network = dict()

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

def extract_linked_wiki_concepts(wiki_body):
    wiki_concepts_dict = dict()
    wikicode = mwparserfromhell.parse(wiki_body)
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
                str_node = node.text
                if str_node == None:
                    str_node = node.title
                wiki_concept = node.title.strip().lower()
            if type(node) == mwparserfromhell.nodes.wikilink.Wikilink:
                surface_form = extract_plain_text(str_node).strip().lower()
                i = 0
                for l in surface_form[::-1]:
                    if l in string.punctuation:
                        i = i - 1
                    else:
                        break
                if i < 0:
                    cleaned_surface_form = surface_form[:i].strip()
                else:
                    cleaned_surface_form = surface_form
                wiki_concepts_dict.setdefault(wiki_concept, set())
                wiki_concepts_dict[wiki_concept].add(cleaned_surface_form)
            wiki_concepts_dict = dict(wiki_concepts_dict.items() + extract_linked_wiki_concepts(str_node).items())
    return wiki_concepts_dict


threshold = 5.79904609897e-05
interested_wiki_concepts = set()
with open(interested_wiki_concepts_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        if float(elements[1]) >= threshold:
            interested_wiki_concepts.add(elements[0].strip().lower())
print "In total there exists " + str(len(interested_wiki_concepts)) + " wiki pages."
wiki_network_to_be = dict()
iterparse = ET.iterparse(wikipedia_file)
i = 0
for event, elem in iterparse:
    if elem.tag.endswith("title"):
        title = elem.text.strip().lower()
    if elem.tag.endswith("text"):
        if title not in interested_wiki_concepts:
            elem.clear()
            continue
        wiki_body = elem.text
        linked_wiki_concepts = extract_linked_wiki_concepts(wiki_body)
        for (wiki_concept, surface_forms) in linked_wiki_concepts.iteritems():
            wiki_network_to_be[(title, wiki_concept)] = surface_forms
        i += 1
        if i != 0 and i % 100 == 0:
            print "Finish scanning interested " + str(i) + " wiki pages."
    elem.clear()

count = 0
for (wiki_concept_a, wiki_concept_b) in wiki_network_to_be.iterkeys():
    if wiki_concept_a < wiki_concept_b:
        if (wiki_concept_b, wiki_concept_a) in wiki_network_to_be:
            for concept_a in wiki_network_to_be[(wiki_concept_a, wiki_concept_b)]:
                for concept_b in wiki_network_to_be[(wiki_concept_b, wiki_concept_a)]:
                    wiki_network[(clean_concept(concept_a), clean_concept(concept_b))] = 1
                    count += 1
                    if count % 10000 == 0:
                        print count
print "Finish building concept reference newtork from wikipedia with " + str(count) + " links."



con = mdb.connect(host=server_url, port=1720, user='wiki', passwd='ontology', db='wiki_ontology');
cursor = con.cursor()

def allindices(string, sub):
    offset = 0
    listindex = []
    i = string.find(sub, offset)
    while i >= 0:
        listindex.append(i)
        i = string.find(sub, i + 1)
    return listindex

count = 0
window_size = 3
for (document_id, concepts) in corpus_concept_pool.iteritems():
    cursor.execute("SELECT abstract FROM dblp_wikification WHERE id = %s", (document_id, ))
    row = cursor.fetchone()
    abstract = row[0].lower()
    abstract_concept_index = dict()
    for concept in concepts:
        for surface_form in concept_dict[concept]:
            indices = allindices(abstract, surface_form)
            for index in indices:
                abstract_concept_index[index] = concept
    sorted_concept_index = sorted(abstract_concept_index.items(), key=lambda k: k[0])
    duplicate_concept_pair = set()
    for i in range(len(sorted_concept_index) - window_size + 1):
        concepts_pool = set()
        for j in range(window_size):
            concepts_pool.add(sorted_concept_index[i + j][1])
        for concept_a in concepts_pool:
            for concept_b in concepts_pool:
                if concept_a < concept_b and concept_a in concept_weight_dict and concept_b in concept_weight_dict and (concept_a, concept_b) not in duplicate_concept_pair:
                    corpus_network.setdefault((concept_a, concept_b), 0)
                    corpus_network[(concept_a, concept_b)] += 1
                    duplicate_concept_pair.add((concept_a, concept_b))
                    count += 1
                    if count % 10000 == 0:
                        print count
# to_remove_list = list()
# for (concept_pair, weight) in corpus_network.iteritems():
#   if weight < 2:
#       count -= 1
#       to_remove_list.append(concept_pair)
# for element in to_remove_list:
#   del corpus_network[element]
print "Finish building concept co-occurence newtork (with sliding window) from document corpus with " + str(count) + " links."


concept_weight_dict.clear()
for (concept_a, concept_b) in wiki_network.iterkeys():
    concept_weight_dict.setdefault(concept_a, [0, 0, 0])
    concept_weight_dict[concept_a][0] += 1
    concept_weight_dict.setdefault(concept_b, [0, 0, 0])
    concept_weight_dict[concept_b][0] += 1
for (concept_a, concept_b) in corpus_network.iterkeys():
    concept_weight_dict.setdefault(concept_a, [0, 0, 0])
    concept_weight_dict[concept_a][2] += 1
    concept_weight_dict.setdefault(concept_b, [0, 0, 0])
    concept_weight_dict[concept_b][2] += 1

concept_node_id_dict = dict()
index = 1
with open(concepts_id_map_file, 'w') as output:
    for concept in concept_weight_dict.iterkeys():
        concept_node_id_dict[concept] = index
        output.write(str(index) + '\t' + concept + '\t' + str(concept_weight_dict[concept][0]) + '\t' + str(concept_weight_dict[concept][1]) + '\t' + str(concept_weight_dict[concept][2]) + '\n')
        index += 1
print "Finish indexing concepts."

with open(corpus_network_file, 'w') as output:
    for (node_pair, link_weight) in corpus_network.iteritems():
        if node_pair[0] in concept_weight_dict and node_pair[1] in concept_weight_dict:
            output.write(str(concept_node_id_dict[node_pair[0]]) + '\t' + str(concept_node_id_dict[node_pair[1]]) + '\t' + str(link_weight) + '\t' + node_pair[0] + '\t' + node_pair[1] + '\n')
print "Finish writing file of concept network from document corpus."

with open(wiki_network_file, 'w') as output:
    for (node_pair, link_weight) in wiki_network.iteritems():
        if node_pair[0] in concept_weight_dict and node_pair[1] in concept_weight_dict:
            output.write(str(concept_node_id_dict[node_pair[0]]) + '\t' + str(concept_node_id_dict[node_pair[1]]) + '\t' + str(link_weight) + '\t' + node_pair[0] + '\t' + node_pair[1] + '\n')
print "Finish writing file of concept network from wikipedia."
