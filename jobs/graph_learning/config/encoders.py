# Use ordinal encoding to capture hierarchy in ranks
# Reference: Supplementary Table S3
# https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7408187/#sup1

TAXON_RANK_LABELS = {
    'no rank': 0,
    'environmental samples': 0,
    'unclassified sequences': 0,
    'unclassified': 0,
    'incertae sedis': 0,
    'clade': 0,
    'superkingdom': 1,
    'kingdom': 2,
    'subkingdom': 3,
    'superphylum': 4,
    'superdivision': 4,
    'phylum': 5,
    'division': 5,
    'subphylum': 6,
    'subdivision': 6,
    'infraphylum': 7,
    'infradivision': 7,
    'superclass': 8,
    'class': 9,
    'subclass': 10,
    'infraclass': 11,
    'cohort': 12,
    'subcohort': 13,
    'superorder': 14,
    'order': 15,
    'suborder': 16,
    'infraorder': 17,
    'parvorder': 18,
    'superfamily': 19,
    'family': 20,
    'subfamily': 21,
    'tribe': 22,
    'subtribe': 23,
    'genus': 24,
    'subgenus': 25,
    'section': 26,
    'subsection': 27,
    'series': 28,
    'subseries': 29,
    'species group': 30,
    'species subgroup': 31,
    'species': 32,
    'forma specialis': 33,
    'special form': 33,
    'subspecies': 34,
    'varietas': 35,
    'morph': 35,
    'form': 35,
    'subvariety': 36,
    'forma': 37,
    'serogroup': 38,
    'pathogroup': 38,
    'serotype': 39,
    'biotype': 39,
    'genotype': 39,
    'strain': 40,
    'isolate': 41,
}