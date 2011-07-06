#!/usr/bin/python
"""
generate_rxnorm_file.py

Extracts RXNORM from the UMLS and converts it to a format that is usable by the
medication reconciliation algorithm. 

Pass your Metathesaurus directory (the one containing .RRF files) as the first 
argument and the output filename as the second parameter (recommended: 
rxnorm.pickle.bz2)

Created by Jorge Herskovic 
Copyright (c) 2011 UTHealth School of Biomedical Informatics. All rights reserved.
"""
import rxnorm
import sys
import os.path
import random
import cPickle as pickle
import bz2

def display_count(count, dot_threshold=1000, pipe_threshold=10000, 
                  newline_threshold=50000, output_stream=sys.stderr):
    if count % dot_threshold == 0:
        output_stream.write(".")
        output_stream.flush()
    if count % pipe_threshold == 0:
        output_stream.write("|")
        output_stream.flush()
    if count % newline_threshold == 0:
        print >>output_stream, " %d" % count
        output_stream.flush()
    
print >>sys.stderr, "Reading Semantic Types"
sty_filename=os.path.join(sys.argv[1], "MRSTY.RRF")
sty_file=open(sty_filename, 'rU')
types={}
count=0
for line in sty_file:
    st=rxnorm.SemanticTypeLine(line)
    if st.CUI in types:
        types[st.CUI].add(st.semtype)
    else:
        types[st.CUI]=set([st.semtype])
    count+=1
    display_count(count)
    
print >>sys.stderr

print  >>sys.stderr, "Reading concepts"
conso_filename=os.path.join(sys.argv[1], "MRCONSO.RRF")
conso_file=open(conso_filename, "rU")
concepts={}
count=0

for line in conso_file:
    if 'RXNORM' not in line:
       continue
    c=rxnorm.Drug(line)
    c.semtypes=types[c.CUI]
    concepts[c.CUI]=c
    count+=1
    display_count(count)

print >>sys.stderr, "\nForgetting semantic type db"
del types

print >>sys.stderr, "Reading relations"
rel_filename=os.path.join(sys.argv[1], "MRREL.RRF")
rel_file=open(rel_filename, "rU")
count=0
relations=[]

for line in rel_file:
    if 'RXNORM' not in line:
        continue
    try:
        r=rxnorm.Relation(line, concepts)
    except:
        sys.stderr.write("!")
        continue
    if r.relation is not None:
        relations.append(r)
    count+=1
    display_count(count)
print >>sys.stderr
    
print >>sys.stderr, len(concepts), "concepts and", len(relations), "relations."
print >>sys.stderr, 'Building indices.'
ingredients={}
ingredient_rel=set(["ingredient_of",
                    "precise_ingredient_of",
                    # rxnorm.relation_kinds.index("has_tradename"),
                   ])

count=0
for r in relations:
    if r.relation in ingredient_rel:
        if r._concept1.CUI in ingredients:
            ingredients[r._concept1.CUI].add(r._concept2)
        else:
            ingredients[r._concept1.CUI]=set([r._concept2])
    count+=1
    display_count(count)
print >>sys.stderr

concept_names={}
for c in concepts:
    cn=concepts[c]._name.lower()
    if cn in concept_names:
        concept_names[cn].add(c)
    else:
        concept_names[cn]=set([c])

print >>sys.stderr, "Ingredients for 10 random drugs:"
for x in [random.choice(ingredients.keys()) for x in xrange(10)]:
    print >>sys.stderr, "Ingredients for", concepts[x]._name ,":", [y for y in ingredients[x]]
    print >>sys.stderr, "Ingredients that are Pharmacologic Substances for", concepts[x]._name ,":", ', '.join( y._name for y in ingredients[x] if 'Pharmacologic Substance' in y.semtypes)
    print
    
zoloft=concept_names['zoloft']
for z in zoloft:
    print >>sys.stderr, "Ingredients for", concepts[z]._name ,":", [y for y in ingredients[z] ]

print >>sys.stderr, "Saving to",sys.argv[2]
r=rxnorm.RXNORM(concepts, relations, ingredients)
pickle.dump(r, bz2.BZ2File(sys.argv[2], 'wb'), pickle.HIGHEST_PROTOCOL)
