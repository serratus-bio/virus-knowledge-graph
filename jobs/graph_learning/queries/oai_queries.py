from datasources.oai import get_llm_response

import json
import re

from json_repair import repair_json


def try_parse_json_object(input):
    """JSON cleaning and formatting utilities."""
    # Sometimes, the LLM returns a json string with some extra description, this function will clean it up.

    result = None
    try:
        # Try parse first
        result = json.loads(input)
    except json.JSONDecodeError:
        print("Warning: Error decoding faulty json, attempting repair")

    if result:
        return input, result

    _pattern = r"\{(.*)\}"
    _match = re.search(_pattern, input, re.DOTALL)
    input = "{" + _match.group(1) + "}" if _match else input

    # Clean up json string.
    input = (
        input.replace("{{", "{")
        .replace("}}", "}")
        .replace('"[{', "[{")
        .replace('}]"', "}]")
        .replace("\\", " ")
        .replace("\\n", " ")
        .replace("\n", " ")
        .replace("\r", "")
        .strip()
    )

    # Remove JSON Markdown Frame
    if input.startswith("```json"):
        input = input[len("```json") :]
    if input.endswith("```"):
        input = input[: len(input) - len("```")]

    try:
        result = json.loads(input)
    except json.JSONDecodeError:
        # Fixup potentially malformed json string using json_repair.
        input = str(repair_json(json_str=input, return_objects=False))

        # Generate JSON-string output using best-attempt prompting & parsing techniques.
        try:
            result = json.loads(input)
        except json.JSONDecodeError:
            print(f"error loading json, json={input}")
            return input, {}
        else:
            if not isinstance(result, dict):
                print(f"not expected dict type. type={type(result)}")
                return input, {}
            return input, result
    else:
        return input, result


def get_bioproject_summary(bioProjectIds, bioProjectTitles, bioProjectDescriptions):
    conversation = []

    instructions_prompt = '''
        ---Role---
        
        You are a helpful bioinformatics research assistant agent being used to summarize datasets in order to retain maximal information.

        ---Goal---
        
        Follow the instructions to summarize BioProjects:
        1. Provide a succinct overview of the high-level ideas covered by the bioproject titles, names, and descriptions, no longer than a paragraph.
        2. For each overarching topic in the summarization, cite all relevant bioproject ID(s).
        3. DO NOT reference any bioprojects that aren't given in the list.
        4. ONLY use the information provided in the bioprojects to generate the summary.
        5. Avoid using any external information or knowledge.

        ---Real Data---
        <documents>
    '''
    bioproject_merged = list(zip(bioProjectIds, bioProjectTitles, bioProjectDescriptions))
    max_len = 10000
    bioprojects_prompt = ''
    for bioproject in bioproject_merged:
        bioprojects_prompt += f'''
            **{bioproject[0]}**: {bioproject[1]} - {bioproject[2]} \n
        '''
        if len(bioprojects_prompt) > max_len:
            bioprojects_prompt = ''
            break
    if len(bioprojects_prompt) == 0:
        for bioproject in bioproject_merged:
            bioprojects_prompt += f'''
                **{bioproject[0]}**: {bioproject[1]}  \n
            '''
            if len(bioprojects_prompt) > max_len:
                break
        
    bioprojects_prompt += '</documents>'
    conversation.append({
        "role": "system",
        "content": instructions_prompt
    })
    conversation.append({
        "role": "user",
        "content": bioprojects_prompt
    })
    response = get_llm_response(conversation)

    return response


def get_community_summary(
        geo_attr_values,
        geo_biomes,
        bioproject_ids,
        bioproject_titles,
        bioproject_desc,
        stat_host_counts,
        host_label_counts,
        disease_counts,
        tissue_counts,
        sotu_species_counts,
        sotu_family_counts,
):
    geo_attr_str = '\n - '.join(geo_attr_values)
    geo_biomes_str = '\n - '.join(geo_biomes)
    bioproject_ids_str = '\n - '.join(bioproject_ids)
    bioproject_titles_str = '\n - '.join(bioproject_titles)
    bioproject_desc_str = '\n - '.join(bioproject_desc)

    # handle None values
    host_label_str = json.dumps(host_label_counts.to_json()) if host_label_counts is not None else ''
    stat_host_str = json.dumps(stat_host_counts.to_json()) if stat_host_counts is not None else ''
    disease_str = json.dumps(disease_counts.to_json()) if disease_counts is not None else ''
    tissue_str = json.dumps(tissue_counts.to_json()) if tissue_counts is not None else ''
    sotu_species_str = json.dumps(sotu_species_counts.to_json()) if sotu_species_counts is not None else ''
    sotu_family_str = json.dumps(sotu_family_counts.to_json()) if sotu_family_counts is not None else ''

    # get bioproject summary
    bioproject_summary = get_bioproject_summary(bioproject_ids_str, bioproject_titles_str, bioproject_desc_str)

    instructions_prompt = f'''
    ---Role---

    You are a helpful bioinformatics research assistant agent being used to interpret massive amounts data.

    ---Goal---
    Write a comprehensive assessment report of a community taking on the role of a bioinformatics research assistant agent. 
    The content of this report includes an overview of the community's key entities and relationships.

    ---Report Structure---
    The report should include the following sections:
    - TITLE: Community's name that represents its key entities - title should be short but specific. When possible, include representative named entities in the title.
    - LABEL: Two words that describe the the community's primary focus or theme of the form "<organsim> <topic>".
    - SUMMARY: An executive summary of the community's overall structure, how its entities are related to each other, and significant points associated with its entities.
    - DETAILED FINDINGS: A list of 5-10 key insights about the community. Each insight should have a short summary followed by multiple paragraphs of explanatory text grounded according to the grounding rules below. Be comprehensive.

    Return output as a well-formed JSON-formatted string with the following format. Don't use any unnecessary escape sequences. The output should be a single JSON object that can be parsed by json.loads.
        {{
            "title": "<report_title>",
            "label": "<community_label>",
            "summary": "<executive_summary>",
            "findings": "[{{"summary":"<insight_1_summary>", "explanation": "<insight_1_explanation"}}, {{"summary":"<insight_2_summary>", "explanation": "<insight_2_explanation"}}]"
        }}

    ---Grounding Rules---
    After each paragraph, add data references if the content of the paragraph was derived from one or more data records. Reference is in the format of [Filters: {{{{<recordKey>: <recordValue>}}}} ... )]. If there are more than 10 data records, show the top 10 most relevant records.
    Each paragraph should contain multiple sentences of explanation and concrete examples with specific named entities. All paragraphs must have these references at the start and end. Use "NONE" if there are no related roles or records. Everything should be in English.

    Example paragraph with references added:
    This is a paragraph of the output text [Filters: {{{{family: Fiersviridae}}}}, {{{{tissue: embryonic brain}}}}]
    
    Any provided filters must be an exact match of one of the following keys:
    - "label": Organism label provided to the run sample.
    - "runId": Run ID associated with the sequence sample.
    - "biosample": The biosample ID associated with the run sample.
    - "bioproject": The BioProject ID associated with the run and biosample.
    - "species": Virus species associated with the run sample.
    - "family": Virus family associated with the run sample.
    - "community": Community ID of the set of clustered run samples.
    - "geography": Geographic attribute from the sample.
    - "biome": Biome code metadata provided with the biosample.
    - "tissue": Tissue metadata provided with the biosample.
    - "disease": The disease metadata provided with the biosample.
    - "statOrganism": Organism inferred from kmer statiscal analysis of the run sample.
    - "sex": Sex metadata provided with the biosample.
    '''

    data_prompt = f'''
    ---Real Data---

    Use the following text for your answer. Do not make anything up in your answer.

    <documents>

    Viruses:
    - Species: {sotu_species_str}
    - Families: {sotu_family_str}

    Organisms:
    - Organism metadata label: {host_label_str}
    - STAT k-mer organisms: {stat_host_str}

    Diseases:
    - {disease_str}

    Tissues:
    - {tissue_str}

    Bioprojects:
    - {bioproject_summary}

    Geo Attributes:
    - {geo_attr_str}

    Geo Biomes:
    - {geo_biomes_str}
    </documents>
    '''

    conversation = []
    conversation.append({
        "role": "system",
        "content": instructions_prompt
    })
    conversation.append({
        "role": "user",
        "content": data_prompt
    })
    response = get_llm_response(conversation)
    return response

