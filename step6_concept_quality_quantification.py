# -*- coding: UTF-8 -*-
#### this script caculates the qualities of concepts based on Wikipedia

import xml.etree.ElementTree as ET 
import mwparserfromhell
import string
import operator
import re
import base64

concepts_list_file = 'results/CValue_ALGORITHM.txt'
interested_wiki_concepts_file = "results/wiki_page_rank.txt"
wikipedia_file = 'enwiki-20110115-pages-articles.xml'
concepts_quality_file = "results/concepts_quality.txt"
concepts_id_map_file = 'results/concepts_id.txt'
concepts_quality_for_matlab_file = "results/concepts_quality_for_matlab.txt"
stop_words_file = "results/stopwords.txt"

wiki_concepts_dict = dict()
concept_freq_dict = dict()
concept_salient_dict = dict()
surface_form_concept_dict = dict()
concept_wiki_concept_dict = dict()

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

concept_dict = dict()
i = 0
with open(concepts_list_file, 'r') as input:
    for line in input:
        if line[0] != '#':
            i += 1
            elements = line.split('\t')
            phrases = elements[0].split('|')
            concept = clean_concept(phrases[0].strip().lower())
            surface_forms = set()
            concept_dict.setdefault(concept, set())
            for phrase in phrases[1:]:
                surface_forms.add(phrase.strip().lower())
            for surface_form in surface_forms:
                concept_dict[concept].add(surface_form)
            concept_salient_dict[concept] = 0
            concept_freq_dict[concept] = 0
            if i != 0 and i % 10000 == 0:
                print "Finish scanning " + str(i) + " concepts."
        else:
            elements = line.split('#')
            for element in elements:
                document_id = element.strip()
                if document_id != "":
                    if not document_id.isdigit():
                        try:
                            wiki_title = base64.urlsafe_b64decode(document_id)
                            wiki_title = wiki_title.strip().lower()
                        except Exception:
                            continue
                        wiki_concepts_dict.setdefault(wiki_title, set())
                        wiki_concepts_dict[wiki_title].add(concept)
print "Finish reading in concepts and their surface_forms."


concept_id_map = dict()
with open(concepts_id_map_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        concept_id_map[elements[1].strip().lower()] =  int(elements[0])

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


def stat_concepts(extracted_concepts, salient_surface_forms):
    for concept in extracted_concepts:
        surface_forms = concept_dict[concept]
        concept_freq_dict[concept] += 1
        for surface_form in surface_forms:
            if surface_form in salient_surface_forms:
                concept_salient_dict[concept] += 1
                if len(salient_surface_forms[surface_form]) != 0:
                    concept_wiki_concept_dict.setdefault(concept, dict())
                    for wiki_concept in salient_surface_forms[surface_form]:
                        concept_wiki_concept_dict[concept].setdefault(wiki_concept, 0)
                        concept_wiki_concept_dict[concept][wiki_concept] += 1
                        
def extract_linked_wiki_concepts(wiki_body):
    salient_surface_forms = dict()
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
                surface_form = clean_concept(extract_plain_text(str_node).strip().lower())
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
                salient_surface_forms.setdefault(cleaned_surface_form, set())
                salient_surface_forms[cleaned_surface_form].add(wiki_concept)
            salient_surface_forms = dict(salient_surface_forms.items() + extract_linked_wiki_concepts(str_node).items())
    return salient_surface_forms


def extract_salient_surface_forms(wiki_body):
    salient_surface_forms = dict()
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
            if type(node) == mwparserfromhell.nodes.wikilink.Wikilink:
                salient_surface_forms.setdefault(cleaned_surface_form, set())
                salient_surface_forms[cleaned_surface_form].add(wiki_concept)
            else:
                salient_surface_forms.setdefault(cleaned_surface_form, set())
            salient_surface_forms = dict(salient_surface_forms.items() + extract_salient_surface_forms(str_node).items())
    return salient_surface_forms

# text = """In [[machine learning]], '''support vector machines''' ('''SVMs''', also '''support vector networks'''<ref name="CorinnaCortes"/>) are [[supervised learning]] models with associated learning [[algorithm]]s that analyze data and recognize patterns, used for [[Statistical classification|classification]] and [[regression analysis]].  Given a set of training examples, each marked as belonging to one of two categories, an SVM training algorithm builds a model that assigns new examples into one category or the other, making it a non-[[probabilistic logic|probabilistic]] [[binary classifier|binary]] [[linear classifier]]. An SVM model is a representation of the examples as points in space, mapped so that the examples of the separate categories are divided by a clear gap that is as wide as possible. New examples are then mapped into that same space and predicted to belong to a category based on which side of the gap they fall on."""
# print set(stat_salient_concepts(text))
# handle Wikipedia

threshold = 5.8e-05
interested_wiki_concepts = set()
with open(interested_wiki_concepts_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        if float(elements[1]) >= threshold:
            interested_wiki_concepts.add(elements[0].strip().lower())

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
        if title in wiki_concepts_dict:
            salient_surface_forms = extract_linked_wiki_concepts(wiki_body)
            if "" in salient_surface_forms:
                del salient_surface_forms[""]
            stat_concepts(wiki_concepts_dict[title], salient_surface_forms)
        i += 1
        if i != 0 and i % 100 == 0:
            print "Finish scanning interested " + str(i) + " wiki pages."
    elem.clear()

sorted_concept_freq_dict = sorted(concept_freq_dict.iteritems(), key=operator.itemgetter(1), reverse=True)
with open(concepts_quality_file, 'w') as output:
    for (concept, freq) in sorted_concept_freq_dict:
        if freq == 0:
            continue
        quality = float(concept_salient_dict[concept]) / float(freq)
        output.write(concept + '\t' + str(freq) + '\t' + str(concept_salient_dict[concept]) + '\t' + str(quality))
        if concept in concept_wiki_concept_dict:
            wiki_concepts = concept_wiki_concept_dict[concept]
            for (wiki_concept, freq) in wiki_concepts.iteritems():
                output.write('\t' + wiki_concept.encode("utf8") + ": " + str(freq))
        output.write('\n')
with open(concepts_quality_for_matlab_file, 'w') as output:
    for (concept, freq) in sorted_concept_freq_dict:
        if freq == 0:
            continue
        quality = float(concept_salient_dict[concept]) / float(freq)
        if concept in concept_id_map:
            output.write(str(concept_id_map[concept]) + '\t' + str(freq) + '\t' + str(concept_salient_dict[concept]) + '\t' + str(quality))
            output.write('\n')
        else:
            print "Not in concept_id_map"
