from owlready2 import get_ontology


def get_bto_ontology():
    return get_ontology('http://purl.obolibrary.org/obo/bto.owl').load()
