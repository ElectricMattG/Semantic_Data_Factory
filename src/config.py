"""
Config provides a number of parameters from app level, defining retries, to
api level parametrisation: parameters and prompt. Input and output data
filepaths are also defined.
"""

import os
import datetime


KICK_OFF = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")

WORKSTREAM = "embed"  # !! NOTE Define the WORKSTREAM HERE !! "generate" or "embed"
defaults = {
    "account": {
        "api_key": "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",
    },
    "api_performance_data": {
        "performance_data_fullpath": ROOT_DIR
        + "/data/"
        + KICK_OFF
        + "_"
        + WORKSTREAM.upper()
        + "/api_performance_data/api_dat_",
    },
    "app": {
        "save_after_calls": 100,
        "max_retries": 3,  # NOTE Where transient handling fails
        "workstream": WORKSTREAM,  # NOTE SET THE PREFERRED WORKSTREAM
        "concur_workers": 10,  # NOTE AT 10 with a sample of 20 rate limiting kicks in
        "max_recs": 1500,
    },
    "exponential_backoff": {
        "max_retries": 3,
        "base_sleep_time": 0.5,
        "max_sleep_time": 5,
        "rand_low": 0.5,
        "rand_hi": 1.5,
    },
    "gpt_embedding_params": {
        "model": "text-embedding-ada-002",  # NOTE this is setup for text completion
        "token_cost_1000": 0.0004,
    },
    "gpt_generate_params": {
        "model": "text-davinci-003",  # NOTE this is setup for text completion
        "temperature": 0,  # NOTE one want's to enforce a file format so 0 temp
        "max_tokens": 3000,  # NOTE output is json so we want to limit the size
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "token_cost_1000": 0.02,
    },
    "input_data": {
        "query_full_filepath": ROOT_DIR
        + "/datasets/esci-data/en_unique_queries_noisey.csv",
    },
    "logging": {
        "format": "| %(asctime)s | %(levelname)s - %(name)-10s - %(message)s",
        "level": 10,
        "output_full_path": ROOT_DIR
        + "/data/"
        + KICK_OFF
        + "_"
        + WORKSTREAM.upper()
        + "/"
        + "/logs/logfile.log",
    },
    "output_data": {
        "results_format": ".json",
        "results_full_filepath": ROOT_DIR
        + "/data/"
        + KICK_OFF
        + "_"
        + WORKSTREAM.upper()
        + "/"
        + "/model_completions/qub_esci_en_locale_",
        "unprocessed_prompts": ROOT_DIR
        + "/data/"
        + KICK_OFF
        + "_"
        + WORKSTREAM.upper()
        + "/"
        + "/unprocessed_prompts/unprocssed_data.json",
    },
    "prompt": {  # NOTE prompting template for query understanding
        "start": "Given these queries: queries = [",
        "instruction": "] Analyze the queries and provide a JSON response with: query, language of query, brand, attributes, color, category, gender, taxonomy_breadcrumbs, product, price, size, and is_book. ",
        "def": "gender is defined as male=His, female=Hers, unisex=Neutral. attributes are text. Always use null=None.",
    },
    "queries_processed_counter": {
        "init": 0,
        "checkpoint": 100,
    },
    "embeddings_processed_counter": {
        "init": 0,
        "checkpoint": 100,
    },
}

# JOB DIRECTORY BUILD
API = "api_performance_data/"
LOGS = "logs/"
COMPLETIONS = "model_completions/"
UNPROCESSED = "unprocessed_prompts/"
JOB_ROOT_DAT = ROOT_DIR + "/data/" + KICK_OFF + "_" + WORKSTREAM.upper() + "/"
os.makedirs(JOB_ROOT_DAT + API)
os.makedirs(JOB_ROOT_DAT + LOGS)
os.makedirs(JOB_ROOT_DAT + COMPLETIONS)
os.makedirs(JOB_ROOT_DAT + UNPROCESSED)
