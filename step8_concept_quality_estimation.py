# -*- coding: UTF-8 -*-
#### this script propagates qualities from LPG to new concepts

concepts_quality_file = "./results/concepts_quality.txt"
concepts_id_map_file = './results/concepts_id.txt'
theta_file = "./results/theta.txt";
gamma_file = "./results/gamma.txt";
lp_quality_file = "./results/lpg_quality.txt"
estimated_concepts_quality_file = "./results/estimated_concepts_quality.txt"

theta = list()
gamma = list()

print "Reading in data regarding theta, gamma"
print
with open(theta_file, 'r') as input:
	for line in input:
		elements = line.split('\t')
		prob = list()
		for element in elements:
			element = element.strip()
			if element != "":
				prob.append(float(element))
		theta.append(prob)

with open(gamma_file, 'r') as input:
	for line in input:
		element = line.strip()
		gamma.append(float(element))

concept_id_map = dict()
concept_freq_map = dict()
with open(concepts_id_map_file, 'r') as input:
	for line in input:
		elements = line.split('\t')
		concept_id_map[int(elements[0]) - 1] = elements[1].strip()
		concept_freq_map[elements[1].strip()] = [int(elements[-3]), int(elements[-1])]

concept_quality_map = dict()
wiki_concepts_set = set()
with open(concepts_quality_file, 'r') as input:
	for line in input:
		elements = line.split('\t')
		concept = elements[0].strip().lower()
		quality = float(elements[3])
		concept_quality_map[concept] = quality
		wiki_concepts_set.add(concept)

num_concepts = len(theta)
print "Number of concepts: " + str(num_concepts)
num_topics = len(theta[0])
print "Number of topics: " + str(num_topics)
print


lp_quality = [0] * num_topics
with open(lp_quality_file, 'r') as input:
	i = 0
	for line in input:
		elements = line.split('\t')
		for element in elements:
			if element.strip() != '':
				lp_quality[i] = float(element)
				i += 1

node_quality = [0] * num_concepts
for i in range(num_concepts):
	for r in range(num_topics):
		node_quality[i] += lp_quality[r] * theta[i][r]

with open(estimated_concepts_quality_file, 'w') as output:
	indices = sorted(range(num_concepts), key=lambda k: -node_quality[k])
	for i in indices:
		if str(concept_id_map[i]) in wiki_concepts_set:
			output.write(str(concept_id_map[i]) + '\t' + str(node_quality[i]) + '\t' + str(concept_quality_map[str(concept_id_map[i])]) + '\t' + '\t' + str(concept_freq_map[str(concept_id_map[i])][0]) + '\t' + str(concept_freq_map[str(concept_id_map[i])][1]) + '\n')
		else:
			output.write(str(concept_id_map[i]) + '\t' + str(node_quality[i]) + '\t' + str(concept_freq_map[str(concept_id_map[i])][0]) + '\t' + str(concept_freq_map[str(concept_id_map[i])][1]) + '*\n')
print "Finish propagation."
