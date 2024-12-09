import os

from openai import AzureOpenAI


def get_oai_client():
    return AzureOpenAI(
        azure_endpoint=os.getenv("OPENAI_ENDPOINT_GPT4_MINI"),
        api_key= os.getenv("OPENAI_TOKEN"),
        api_version="2024-09-01-preview"
    )

def get_llm_response(conversation):
    oai_client = get_oai_client()
    response = oai_client.chat.completions.create(
        # gpt-4o-mini
        model='gpt-4o-mini',
        messages=conversation,
    )
    return response.choices[0].message.content
