from owlready2 import get_ontology


def get_bto_ontology():
    return get_ontology("http://purl.obolibrary.org/obo/bto.owl").load()


def get_doi_ontology():
    return get_ontology(
        "https://raw.githubusercontent.com/DiseaseOntology/HumanDiseaseOntology/refs/heads/main/src/ontology/HumanDO.owl"
    ).load()
