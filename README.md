concept_newtork
===============

Concept Network Construction by Integrating Knowledge Base with Scientific and Technical Corpora

This projects depend on several existing projects including Tagme and Jate. One needs to first apply for the Tagme API and compile Jate before running our code.
Some necessary Python packages are also required mwparserfromhell, networkx and MySQLdb.

For the datasets, please dowanload them from http://arnetminer.org/citation and http://dumps.wikimedia.org/enwiki/

Additionally, some MySQL tables for keeping Wiki surface forms and Wikification results are needed. Interesting readers can refer to their formats in folder "mysql_tables".


Given these preparation done, to construct the network, sequentially run the python code from step0 to step9 (step5 was written in C++ to ensure efficiency).

Note to run Jate immediately after finish step2 in order to generate term extraction results from CValue.
