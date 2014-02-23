# -*- coding: UTF-8 -*-
#### this script does the wikification on papers published in specified venues
import MySQLdb as mdb
import requests
import time

tagme_url = 'http://tagme.di.unipi.it/tag'
api_key = ''    # apply it here: http://tagme.di.unipi.it
dblp_file = 'acm_output.txt'    # download it here: http://arnetminer.org/citation with V6
venue_file = './results/venues_filtered.txt'
database_url = '127.0.0.1' # a mysql table to keep wikification results

venue_set = set()
with open(venue_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        venue_set.add(elements[0].strip())
print "Load venues complete."

def wikification(text):
    parameters = {
        "text": text,
        "key": api_key,
        "include_categories": True
        }
    return requests.get(tagme_url, params=parameters)

con = mdb.connect(host=database_url, port=1720, user='root', passwd='admin', db='wiki_ontology', charset='utf8');
cursor = con.cursor()


i = 0
with open(dblp_file, 'r') as input:
    for line in input:
        try:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("#*"):
                title = decoded_line[2:].strip()
            if decoded_line.startswith("#index"):
                id = int(decoded_line[6:])
            if decoded_line.startswith("#year"):
                year = int(decoded_line[5:])
            if decoded_line.startswith("#conf"):
                venue = decoded_line[5:].strip()
            if decoded_line.startswith("#arnetid"):
                arnetid = int(decoded_line[8:])
            if decoded_line.startswith("#!"):
                abstract = decoded_line[2:].strip()
                i += 1
                # With abstracts, there are in total 19,715 papers.
                if id != 0 and abstract != "" and venue in venue_set:
                    num = cursor.execute("SELECT id FROM dblp_wikification WHERE id = %s", (id, ))
                    if num == 0:
                        result = wikification(abstract)
                        text = result.text.encode('utf-8')
                        time.sleep(1)
                id = 0
                year = 0
                arnetid = 0
                venue = ""
                abstract = ""
                title = ""
                if i != 0 and i % 1000 == 0:
                    print "Finish scanning " + str(i) + " papers."
        except Exception:
            print "error"
            continue