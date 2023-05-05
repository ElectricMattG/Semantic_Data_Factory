import pytest
from unittest.mock import patch, Mock
from src.prompt_builder.prompt_builder import PromptHandler
from src.api_handler.api_handler import APIHandler
from src.api_data_handler.api_data_handler import APIDataHandler
import pandas as pd


@pytest.fixture()
def prompt_handler():
    prompt_handler = PromptHandler
    with patch.object(prompt_handler, 'batch_queries', Mock()):
        with patch.object(prompt_handler, 'build_prompts', Mock()):
            yield prompt_handler()


# GIVEN
def test_prompt_handler_instantiation(prompt_handler):
    # THEN queries are batched and prompts are built
    prompt_handler.batch_queries.assert_called_once()
    prompt_handler.build_prompts.assert_called_once()

    # AND the query data is set and of the correct type
    assert prompt_handler.query_data is not None
    assert type(prompt_handler.query_data) is pd.DataFrame
    
    # AND the approx batch size is set
    assert prompt_handler.approx_batch_size is not None
    assert prompt_handler.approx_batch_size > 0


# GIVEN
def test_batch_queries():
    # WHEN prompt handler instantiated
    prompt_handler = PromptHandler()
    # THEN queries_batched is non-zero
    assert len(prompt_handler.queries_batched) > 0


# GIVEN
def test_build_prompts():
    # WHEN prompt handler instantiated
    prompt_handler = PromptHandler()
    # THEN queries_batched is non-zero
    if (prompt_handler.workstream == "embed") | (prompt_handler.workstream == "generate"):
        assert len(prompt_handler.prompts) > 0
