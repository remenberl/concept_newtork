# -*- coding: UTF-8 -*-
#### this script estimates qualities of LPGs.


omega_file = "./results/omega.txt";
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
gamma_file = "./results/gamma.txt"
gamma = list()
with open(gamma_file, 'r') as input:
    for line in input:
        element = line.strip()
        gamma.append(float(element))

num_topic = len(omega)
topic_coverage_with_quality = [0] * num_topic
topic_coverage_without_quality = [0] * num_topic

import random
concept_quality_dict = dict()
quality_file = "./results/concepts_quality.txt"
test_file = "./results/test.txt"
count = 0
with open(test_file, 'w') as output:
    with open(quality_file, 'r') as input:
        for line in input:
            elements = line.split('\t')
            freq = int(elements[1])
            concept = elements[0].strip()
            if freq >= 10:
                if random.random() > 0.7:
                    concept_quality_dict[concept] = float(elements[3])
                else:
                    output.write(concept + '\t' + str(float(elements[3])) + '\n')

concept_id_map = dict()
concepts_id_map_file = './results/concepts_id.txt'
with open(concepts_id_map_file, 'r') as input:
    for line in input:
        elements = line.split('\t')
        concept_id_map[int(elements[0])] = elements[1].strip()


theta_file = "./results/theta.txt";
theta = list()
id = 0
with open(theta_file, 'r') as input:
    for line in input:
        id += 1
        elements = line.split('\t')
        prob = list()
        for element in elements:
            element = element.strip()
            if element != "":
                prob.append(float(element))
        theta.append(prob)


topic_quality = [0] * num_topic
normalizer = [0] * num_topic

import math
for i in range(len(theta)):
    if concept_id_map[i + 1] in concept_quality_dict:
        quality = concept_quality_dict[concept_id_map[i + 1]]
        for r in range(num_topic):
            if math.isnan(theta[i][r]):
                continue
            topic_quality[r] += gamma[i] * quality * theta[i][r]
            normalizer[r] += gamma[i] *  theta[i][r]
for r in range(num_topic):
    if normalizer[r] == 0:
        print topic_quality[r]
        continue
    topic_quality[r] /= normalizer[r]

lp_quality_file = "./results/lpg_quality.txt"
with open(lp_quality_file, 'w') as ouput:
    for r in range(num_topic):
        ouput.write(str(topic_quality[r]))
        ouput.write('\t')


