import re

from datasources.owl import get_bto_ontology, get_doi_ontology

import pandas as pd
import dask.dataframe as dd
from owlready2 import (
    owl,
    Restriction,
    ThingClass,
)
import spacy
from spacy.matcher import Matcher
from spacy.tokenizer import Tokenizer


def get_tissue_nodes_df():
    onto = get_bto_ontology()
    rows_list = [{"bto_id": c.name, "name": c.label.first()} for c in onto.classes()]
    df = pd.DataFrame(rows_list, columns=["bto_id", "name"])
    return dd.from_pandas(df, npartitions=1)


def get_tissue_edges_df():
    onto = get_bto_ontology()
    rows_list = []

    for bto_obj in onto.classes():
        for bto_parent_class in set(bto_obj.is_a):
            # Ignore the root/parent class
            if bto_parent_class == owl.Thing:
                continue
            else:
                bto_obj_type = type(bto_parent_class)
                if bto_obj_type == ThingClass:
                    rows_list.append(
                        {
                            "bto_id": bto_obj.name,
                            "parent_bto_id": bto_parent_class.name,
                        }
                    )
                elif bto_obj_type == Restriction:
                    # Restriction 2202 defines a derives_from/develops_from relationship
                    rows_list.append(
                        {
                            "bto_id": bto_obj.name,
                            "parent_bto_id": bto_parent_class.value.name,
                        }
                    )
    df = pd.DataFrame(rows_list, columns=["bto_id", "parent_bto_id"])
    return dd.from_pandas(df, npartitions=1)


def get_disease_nodes_df():
    onto = get_doi_ontology()
    rows_list = [{"do_id": c.name, "name": c.label.first()} for c in onto.classes()]
    df = pd.DataFrame(rows_list, columns=["do_id", "name"])
    return dd.from_pandas(df, npartitions=1)


def get_disease_edges_df():
    onto = get_doi_ontology()
    rows_list = []

    for do_obj in onto.classes():
        for do_parent_class in set(do_obj.is_a):
            # Ignore the root/parent class
            if do_parent_class == owl.Thing:
                continue
            else:
                do_obj_type = type(do_parent_class)
                if do_obj_type == ThingClass:
                    rows_list.append(
                        {
                            "do_id": do_obj.name,
                            "parent_do_id": do_parent_class.name,
                        }
                    )
                elif do_obj_type == Restriction:
                    # Restriction 2202 defines a derives_from/develops_from relationship
                    rows_list.append(
                        {
                            "do_id": do_obj.name,
                            "parent_do_id": do_parent_class.value.name,
                        }
                    )
    df = pd.DataFrame(rows_list, columns=["do_id", "parent_do_id"])
    return dd.from_pandas(df, npartitions=1)


def get_disease_to_ontology():
    # Load the ontology and create a dictionary of classes and synonyms
    onto = get_doi_ontology()

    def preprocess(input_str):
        punct_pattern = r"\ *[_&<>:-]+\ *"
        input_str = re.sub(punct_pattern, " ", input_str)
        return str(input_str).lower().strip()

    onto_map = {c.name: c.label.first() for c in onto.classes()}
    onto_synonyms = {
        c.name: c.hasExactSynonym + c.hasRelatedSynonym for c in onto.classes()
    }

    # Remove generic terms to avoid false positives
    ## Cancer
    del onto_map["DOID_162"]
    del onto_synonyms["DOID_162"]
    ## Disease
    del onto_map["DOID_4"]
    del onto_synonyms["DOID_4"]
    ## Syndrome
    del onto_map["DOID_225"]
    del onto_synonyms["DOID_225"]

    onto_synonyms["DOID_14221"] += [
        "metabolic syndrome"
    ]  # missing synonym available on website
    onto_synonyms["DOID_2945"] += ["sars", "cov"]  # common lowercased synonyms

    # create a inverse mapping of classes and synonyms to ontology IDs
    onto_inverse = {
        preprocess(c.label.first()): c.name for c in onto.classes() if c.label != []
    }
    onto_synonyms_reverse = {
        preprocess(s): c for c, syn in onto_synonyms.items() for s in syn
    }
    onto_map_inverse = {**onto_inverse, **onto_synonyms_reverse}

    assert len(onto_map) == len(onto_synonyms)
    print("Number of classes:", len(onto_map))

    class_labels = {str(c) for c in onto_map.values() if c is not None}
    onto_synonyms_flattend = {str(s) for syn in onto_synonyms.values() for s in syn}
    onto_terms = class_labels.union(onto_synonyms_flattend)

    return onto_terms, onto_map, onto_map_inverse


def get_disease_ontology_matcher(onto_terms):
    # spacy.cli.download('en_core_web_lg')
    nlp = spacy.load("en_core_web_lg")

    # include the ontology values in the vocabulary
    for value in onto_terms:
        nlp.vocab.strings.add(value)

    matcher = Matcher(nlp.vocab)
    tokenizer = Tokenizer(nlp.vocab)

    for onto_value in onto_terms:
        patterns = []
        # Handle acronyms: keep the original case to avoid false positives with common words
        if onto_value.isupper() and len(onto_value) <= 12:
            patterns.append(
                [{"TEXT": token.text} for token in tokenizer(str(onto_value))]
            )
        else:
            patterns.append(
                [{"LOWER": token.lower_} for token in tokenizer(str(onto_value))]
            )

        # 'FUZZY' matching: too slow
        # patterns.append([{'LOWER': {'FUZZY2': token.lower_}} for token in tokenizer(str(onto_value))])
        match_id = nlp.vocab.strings[str(onto_value)]
        matcher.add(match_id, patterns, greedy="LONGEST")

    infixes = nlp.Defaults.infixes + [r"[_~]"]
    infix_re = spacy.util.compile_infix_regex(infixes)
    tokenizer.infix_finditer = infix_re.finditer

    return matcher, tokenizer, nlp
