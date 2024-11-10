import os
import xml
import re
import csv
import ast
import time
import pandas as pd
import glob

import dask.dataframe as dd

from datasources.sra import BioSamplesMatcherHandler


SRA_DATA_PATH = "/mnt/graphdata/ncbi-data"
BIOSAMPLES_PATH = f"{SRA_DATA_PATH}/biosample_set.xml"
PARSED_DATA_PATH = f"{SRA_DATA_PATH}/parsed_data"
EXTRACTED_DATA_PATH = f"{SRA_DATA_PATH}/extracted_data"
PARTITION_SIZE = 100000


def fix_column_orders():
    files = glob.glob(f"{PARSED_DATA_PATH}/*.csv")
    desired_columns = ["title", "attributes", "biosample_id", "paragraph"]
    for file in files:
        df = pd.read_csv(file)
        if list(df.columns) != desired_columns:
            df = df.reindex(columns=desired_columns)
            df.to_csv(file, index=False)
    

def get_biosamples_df(biosample_path=BIOSAMPLES_PATH):
    if not os.path.exists(biosample_path):
        # TODO: support downloading and unzipping the biosample_set.xml file from NCBI
        raise FileNotFoundError(f"{biosample_path} does not exist")

    if os.path.exists(f"{PARSED_DATA_PATH}"):
        dtype_dict = {
            'title': 'string',
            'attributes': 'string',
            'biosample_id': 'string',
            'paragraph': 'string'
        }
        dask_df = dd.read_csv(
            f"{PARSED_DATA_PATH}/*.csv",
            dtype=dtype_dict,
            quotechar='"',
            escapechar='\\',
            header=0,
            on_bad_lines='warn',
            engine='python',
        )
        return dask_df

    os.makedirs(f"{PARSED_DATA_PATH}")
    parser = xml.sax.make_parser()
    handler = BioSamplesMatcherHandler(
        PARTITION_SIZE,
        PARSED_DATA_PATH,
    )
    parser.setContentHandler(handler)
    parser.parse(biosample_path)
    fix_column_orders()
    dask_df = dd.read_csv(f"{PARSED_DATA_PATH}/*.csv")
    dask_df = dask_df.fillna("")
    return dask_df


def disease_validation(attribute, value):
    numbers_pattern = r"^[\d\. ]*$"
    invalid_values = {
        "not provided",
        "not applicable",
        "not collected",
        "not available",
        "none",
        "undetected",
        "unknown",
        "none detected",
        "na",
        "institute",
        "institute",
        "center",
        "laboratory",
        "lab",
        "submitter",
        "submitter_handle",
        "facility",
        "unit",
        "broker",
        "department",
        "division",
        "group",
        "service",
        "company",
        "corporation",
        "organization",
        "association",
        "lab",
        "facilities",
        "collected_by",
        "collected by",
    }
    if re.match(numbers_pattern, value):
        return False

    if any(term in attribute.lower() for term in invalid_values):
        return False

    # check if attributes contain 'subject is affected' and value is not negative
    if attribute == "subject_is_affected" and value in {
        "no",
        "false",
        "negative",
        "not affected",
        "not positive",
        "0",
        "n",
        "f",
    }:
        return False

    return True


def match_ontology_terms(biosamples_partition, matcher, tokenizer, nlp):
    sample_dict = (
        biosamples_partition.groupby("biosample_id")
        .apply(lambda x: x.to_dict(orient="records")).compute()
    )
    matches_dict = {}

    for biosample_id, content_dict in sample_dict.items():
        content_dict = content_dict[0]
        cur_matches = {}

        title = content_dict.get("title", "")
        title_tokens = tokenizer(title)
        title_matches = matcher(title_tokens, as_spans=True)
        if len(title_matches) > 0:
            cur_matches["title"] = title_matches

        attributes = content_dict.get("attributes", "")
        if type(attributes) == str:
            try:
                attributes = ast.literal_eval(attributes)
                attributes.items()
            except Exception:
                attributes = {}
        else:
            attributes = {}

        attributes = {
            key: value
            for key, value in attributes.items()
            if disease_validation(key, value)
        }

        attributes_tokens = {key: tokenizer(value) for key, value in attributes.items()}
        attribute_matches = {}

        for key, value in attributes_tokens.items():
            attribute_match = matcher(value, as_spans=True)
            if len(attribute_match) > 0:
                attribute_matches[key] = matcher(value, as_spans=True)

        if len(attribute_matches) > 0:
            cur_matches["attributes"] = attribute_matches

        if "paragraph" in content_dict:
            paragraph = str(content_dict['paragraph'])
            paragraph_tokens = tokenizer(paragraph)
            paragraph_matches = matcher(paragraph_tokens, as_spans=True)

            if len(paragraph_matches) > 0:
                cur_matches["paragraph"] = paragraph_matches

        matches_dict[biosample_id] = cur_matches

    return matches_dict


def preprocess(input_str):
    punct_pattern = r"\ *[_&<>:-]+\ *"
    input_str = re.sub(punct_pattern, " ", input_str)
    return input_str.lower().strip()


def write_to_disc(matches_dict, onto_map, onto_map_inverse, index):
    if not os.path.exists(f"{EXTRACTED_DATA_PATH}"):
        os.makedirs(f"{EXTRACTED_DATA_PATH}")

    fname = f"{EXTRACTED_DATA_PATH}/biosample_disease_{index}.csv"

    with open(fname, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["biosample", "source", "text", "do_label", "do_id"])
        for biosample, matches in matches_dict.items():
            source = ""
            text = ""
            do_id = ""
            do_label = ""
            for match_type, match in matches.items():
                if match_type == "attributes":
                    for attribute, match in match.items():
                        source = attribute
                        terms = set([token.text for token in match])
                        text = " ".join(terms)
                        label = match[0].label_
                        do_id = onto_map_inverse.get(preprocess(label), "")
                        do_label = onto_map.get(do_id, "")
                        writer.writerow([biosample, source, text, do_label, do_id])
                if match_type == "title":
                    source = "title"
                    text = " ".join([token.text for token in match])
                    label = match[0].label_
                    do_id = onto_map_inverse.get(preprocess(label), "")
                    do_label = onto_map.get(do_id, "")
                    writer.writerow([biosample, source, text, do_label, do_id])
                if match_type == "paragraph":
                    source = "paragraph"
                    text = " ".join([token.text for token in match])
                    label = match[0].label_
                    do_id = onto_map_inverse.get(preprocess(label), "")
                    do_label = onto_map.get(do_id, "")
                    writer.writerow([biosample, source, text, do_label, do_id])
    return fname


def get_biosample_disease_df():
    if os.path.exists(f"{SRA_DATA_PATH}/biosample_disease.csv"):
        df = dd.read_csv(f"{SRA_DATA_PATH}/biosample_disease.csv", dtype='string', blocksize="1MB")
        return df

    if not os.path.exists(EXTRACTED_DATA_PATH):
        raise FileNotFoundError(f"{EXTRACTED_DATA_PATH} does not exist")

    files = [f for f in os.listdir(f"{EXTRACTED_DATA_PATH}") if f.endswith(".csv")]
    if len(files) == 0:
        raise FileNotFoundError(f"No parsed files found in {EXTRACTED_DATA_PATH}")

    df = dd.read_csv(f"{EXTRACTED_DATA_PATH}/*.csv")
    df.to_csv(f"{SRA_DATA_PATH}/biosample_disease.csv", index=False, single_file=True)
    return df
