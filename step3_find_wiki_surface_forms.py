# -*- coding: UTF-8 -*-
#### this script generates wiki surface froms given the dump of wiki articles

import MySQLdb as mdb
import xml.etree.ElementTree as ET 
import mwparserfromhell

in_file = 'enwiki-20110115-pages-articles.xml'
server_url = '127.0.0.1'

def find_mentioned_concepts(wiki_body):
    if wiki_body == None:
        return None
    index = wiki_body.find("==")
    if index < 0:
        return None
    wikicode = mwparserfromhell.parse(wiki_body[:index])
    links =  wikicode.filter_wikilinks()
    for link in links:
        # print str(link.title) + "\t" + str(link.text)
        title = str(link.title).strip().lower()
        if link.text == None:
            text = title
        else:
            text = str(link.text).strip().lower()
        if title not in surface_forms_dict:
            surface_forms_dict[title] = dict()
            surface_forms_dict[title][text] = 1
        else:
            surface_forms_dict[title][text] = surface_forms_dict[title].get('text', 0) + 1


con = mdb.connect(host=server_url, port=1720, user='root', passwd='admin', db='wiki_ontology');
cursor = con.cursor()
iterparse = ET.iterparse(in_file)
i = 0
surface_forms_dict = dict()
for event, elem in iterparse:
    if elem.tag.endswith("text"):
        find_mentioned_concepts(elem.text)
        i += 1
        if i % 20000 == 0:
            for (title, surface_forms) in surface_forms_dict.iteritems():
                for (surface_form, count) in surface_forms.iteritems():
                    num = cursor.execute("SELECT * FROM surface_forms WHERE title = %s and surface_form = %s", (title, surface_form))
                    if num == 0:
                        cursor.execute("INSERT INTO surface_forms VALUES (%s, %s, %s)", (title, surface_form, count))
                    else:
                        cursor.execute("UPDATE surface_forms SET count = count + %s WHERE title = %s and surface_form = %s", (count, title, surface_form))
            del surface_forms_dict
            surface_forms_dict = dict()
        if i % 5000 == 0:
            print "Finish scanning " + str(i) + " pages."
    elem.clear()
