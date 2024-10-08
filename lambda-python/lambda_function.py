import json
from llama_index.llms.openai import OpenAI
import logging
import sys
import time

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

# llm=OpenAI(model="gpt-4-turbo")
# llm=OpenAI(model="gpt-4o")
llm=OpenAI(model="gpt-3.5-turbo")

def lambda_handler(event, context):
    start = time.perf_counter_ns()
    response = llm.complete("What public transportation might be available in a city?")
    end = time.perf_counter_ns()
    elapsed = (end - start) / 1000.0
    json_response = {
        'output': str(response),
        'runtime': elapsed,
    }
    return {
        'statusCode': 200,
        'body': json_response,
    }
