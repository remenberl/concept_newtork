# -*- coding: UTF-8 -*-
#### this script constructs the final concept network

id_to_concept_map = dict()
concept_to_id_map = dict()
concepts_id_file = 'results/concepts_id.txt'
with open(concepts_id_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        id_to_concept_map[int(elements[0]) - 1] = elements[1].strip()
        concept_to_id_map[elements[1].strip()] = int(elements[0]) - 1
bad_concepts = set()
good_concepts = set()
threshold = 0.1
with open("results/concepts_quality.txt", 'r') as input:
    for line in input:
        elements = line.split('\t')
        quality = float(elements[3])
        freq = int(elements[1])
        if elements[0].strip() in concept_to_id_map:
            id = concept_to_id_map[elements[0].strip()]
            if quality > threshold and freq > 4:
                good_concepts.add(id)
            if quality <= threshold and freq >= 1:
                bad_concepts.add(id)
with open("results/estimated_concepts_quality.txt", 'r') as input:
    for line in input:
        elements = line.split('\t')
        if float(elements[1]) > 0.15:
            id = concept_to_id_map[elements[0].strip()]
            if id not in bad_concepts:
                good_concepts.add(id)
adjacency = dict()
with open('results/corpus_network.txt', 'r') as input:
    for line in input:
        elements = line.split('\t')
        id_a = int(elements[0]) - 1
        id_b = int(elements[1]) - 1
        if id_a not in good_concepts or id_b not in good_concepts:
            continue
        adjacency.setdefault(id_a, set())
        adjacency.setdefault(id_b, set())
        adjacency[id_a].add(id_b)
        adjacency[id_b].add(id_a)
with open('results/wiki_network.txt', 'r') as input:
    for line in input:
        elements = line.split('\t')
        id_a = int(elements[0]) - 1
        id_b = int(elements[1]) - 1
        if id_a not in good_concepts or id_b not in good_concepts:
            continue
        adjacency.setdefault(id_a, set())
        adjacency.setdefault(id_b, set())
        adjacency[id_a].add(id_b)
        adjacency[id_b].add(id_a)

stopwords = set()
stop_words_file = "./results/stopwords.txt"
with open(stop_words_file, 'r') as input:
    for line in input:
        stopwords.add(line.strip())

def clean_concept(concept):
    elements = concept.split(' ')
    if len(elements) > 2 and elements[-1] in stopwords:
        return ' '.join(elements[:-1])
    else:
        return concept
concepts_list_file = 'results/CValue_ALGORITHM.txt'
wiki_concept_pool = dict()
import base64
with open(concepts_list_file, 'r') as input:
    concept = ""
    for line in input:
        if line[0] != '#':
            elements = line.split('\t')
            if float(elements[-1]) <= 0:
                break
            phrases = elements[0].split('|')
            concept = clean_concept(phrases[0].strip().lower())
            if concept in concept_to_id_map:
                concept = concept_to_id_map[concept]
                if concept in good_concepts:
                    continue
            concept = ""
        else:
            if concept == "":
                continue
            elements = line.split('#')
            for element in elements:
                document_id = element.strip()
                if document_id != "":
                    if document_id.isdigit():
                        pass
                    else:
                        try:
                            wiki_title = base64.urlsafe_b64decode(document_id)
                        except Exception:
                            continue
                        wiki_concept_pool.setdefault(wiki_title, set())
                        wiki_concept_pool[wiki_title].add(concept)

import MySQLdb as mdb                            
server_url = '127.0.0.1'
con = mdb.connect(host=server_url, port=1720, user='root', passwd='admin', db='wiki_ontology');
cursor = con.cursor()
i = 0
for (concept, neighbours) in wiki_concept_pool.iteritems():
    i += 1
    cursor.execute("SELECT * FROM surface_forms WHERE title = %s", (concept, ))
    rows = cursor.fetchall()
    surface_forms = set()
    for row in rows:
        title = row[0]
        surface_form = row[1]
        cleaned_concept = clean_concept(surface_form.strip().lower())
        if cleaned_concept not in concept_to_id_map:
            continue
        # print cleaned_concept
        id = concept_to_id_map[cleaned_concept]
        if id in good_concepts:
            surface_forms.add(id)
            for neighbour in neighbours:
                adjacency.setdefault(id, set())
                adjacency.setdefault(neighbour, set())
                adjacency[id].add(neighbour)
                adjacency[neighbour].add(id)
    for id_1 in surface_forms:
        for id_2 in surface_forms:
            adjacency[id_1].add(id_2)
    if i % 500 == 0:
        print "Finish scanning " + str(i) + " pages."

with open('results/nearest_neighbours.txt', 'w') as output:
    for (id, neighbours) in adjacency.iteritems():
        output.write(str(id))
        for neighbour in neighbours:
            output.write('\t' + str(neighbour))  
        output.write('\n')



theta_file = "results/theta.txt";
theta = list()
with open(theta_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        prob = list()
        for element in elements:
            element = element.strip()
            if element != "":
                prob.append(float(element))
        theta.append(prob)
gamma_file = "results/gamma.txt"
gamma = list()
with open(gamma_file, 'r') as input:
    for line in input:
        element = line.strip()
        gamma.append(float(element))
omega_file = "results/omega.txt";
omega = list()
with open(omega_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        prob = list()
        for element in elements:
            element = element.strip()
            if element != "":
                prob.append(float(element))
        omega.append(prob)
adjacency = dict()
with open('results/nearest_neighbours.txt', 'r') as input:
    for line in input:
        elements = line.split('\t')
        adjacency[int(elements[0])] = set()
        for element in elements[1:]:
            adjacency[int(elements[0])].add(int(element))
lp_quality = list()
lp_quality_file = "results/lpg_quality.txt"
with open(lp_quality_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        for element in elements:
            if element.strip() != '':
                lp_quality.append(float(element))
import math
def compute_similarity(theta_a, theta_b, omega, gamma_a, gamma_b):
    num_topic = len(omega)
    sim = 0
    for r in range(num_topic):
        for s in range(num_topic):
            sim += theta_a[r] * theta_b[s]  * omega[r][s]
    return (0.5 - math.log(sim) / (2 * math.log(sim * gamma_a * gamma_b)))

one_hop_sim = dict()
normalization = dict()
for (concept, id) in concept_to_id_map.iteritems():
    if id not in adjacency:
        continue
    result = {}
    for i in adjacency[id]:
        if (i, id) not in one_hop_sim:
            one_hop_sim[(id, i)] = compute_similarity(theta[id], theta[i], omega, gamma[id], gamma[i])
            one_hop_sim[(i, id)] = one_hop_sim[(id, i)]
            normalization.setdefault(id, 0) 
            normalization[id] += one_hop_sim[(i, id)]
        else:
            normalization.setdefault(id, 0) 
            normalization[id] += one_hop_sim[(i, id)]

with open('results/concept_network_links.txt', 'w') as output:
    similarity = dict()
    for (concept, id) in concept_to_id_map.iteritems():
        if id not in adjacency:
            continue
        result = {}
        for i in adjacency[id]:
            if (i, id) not in one_hop_sim:
                result[i] = compute_similarity(theta[id], theta[i], omega, gamma[id], gamma[i])
            else:
                result[i] = one_hop_sim[(i, id)]
        for i in result.iterkeys():
            for j in result.iterkeys():
                if i < j:
                    similarity.setdefault((i, j), 0)
                    similarity[(i, j)] += result[i] * result[j] / normalization[i] / normalization[j]
    for ((i, j), score) in similarity.iteritems():
        output.write(id_to_concept_map[i] + '\t' + id_to_concept_map[j] + '\t')
        output.write(str(similarity[(i, j)]) + '\n')
