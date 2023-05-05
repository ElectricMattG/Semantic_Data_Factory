from src.api_data_handler.api_data_handler import APIDataHandler
from src.prompt_builder.prompt_builder import PromptHandler
from src.api_handler.api_handler import APIHandler
from unittest.mock import MagicMock, patch, Mock
from logging import Logger
import openai
import pytest
from queue import Queue
from src.errors import UnresolvedTransientError


# GIVEN
def test_handler_instantiation():
    # WHEN instantiating the APIDataHandler
    handler = APIDataHandler(APIHandler, PromptHandler)

    # THEN the queues are instantiated and no tasks are present
    assert type(handler.api_handler.results) == Queue
    assert handler.api_handler.results.empty() == True
    assert handler.api_handler.api_latency == None
    assert type(handler.api_handler.latencies) == Queue
    assert handler.api_handler.latencies.empty() == True
    assert handler.api_handler._transient_errors == (
            handler.api_handler.openai_binding.error.Timeout,
            handler.api_handler.openai_binding.error.APIError,
            handler.api_handler.openai_binding.error.RateLimitError,
        )
    
  
def test_successful_retry_logic():
    # GIVEN a prompt string and thread id
    prompt_str = "somestring"
    id = '1'

    # WHEN instantiating the APIDataHandler, a prompt is provided and thread id
    handler = APIDataHandler(APIHandler, PromptHandler)

    # THEN the api is called successfully
    with patch.object(handler.api_handler, 'api_call', Mock()) as api_call:
        handler.api_handler.hello_gpt(prompt_str, id)
        api_call.assert_called_once_with(prompt_str, id)



def test_unsuccessful_transient_retry_logic():
    # GIVEN a prompt string and thread id
    prompt_str = "somestring"
    id = '1'

    # WHEN instantiating the APIDataHandler
    handler = APIDataHandler(APIHandler, PromptHandler)

    # THEN the api is called but raises transient errors
    with patch.object(handler.api_handler, 'api_call', Mock()) as api_call:
        api_call.side_effect = handler.api_handler.openai_binding.error.Timeout()
        # THEN raise UnresolvedTransientError
        with pytest.raises(UnresolvedTransientError):
            handler.api_handler.hello_gpt(prompt_str, id)
        
        api_call.side_effect = handler.api_handler.openai_binding.error.APIError()
        # THEN raise UnresolvedTransientError
        with pytest.raises(UnresolvedTransientError):
            handler.api_handler.hello_gpt(prompt_str, id)

        api_call.side_effect = handler.api_handler.openai_binding.error.RateLimitError()
        # THEN raise UnresolvedTransientError
        with pytest.raises(UnresolvedTransientError):
            handler.api_handler.hello_gpt(prompt_str, id)     


def test_successful_api_call_embed():
    # GIVEN a prompt string and thread id
    prompt_str = "This is a query"
    id = '0'

    # WHEN instantiating the APIDataHandler, a prompt is provided and thread id
    handler = APIDataHandler(APIHandler, PromptHandler)
    handler.api_handler.workstream = "embed"
    handler.api_handler.model = "some model"

    # THEN the embedding end-point is called successfully
    with patch.object(handler.api_handler.openai_binding.Embedding, 'create', Mock()):
        with patch.object(handler.api_handler, 'logger', MagicMock(spec_set=Logger)):
            handler.api_handler.openai_binding.Embedding.create.return_value = MagicMock()
            handler.api_handler.api_call(prompt_str, id)

        # AND the response is set and the latency data is availble
            handler.openai_binding.Embedding.create.assert_called_once()
            assert handler.api_handler.response is not None
            assert handler.api_handler.api_latency is not None


def test_valid_params_api_call_embed():
    # GIVEN a prompt string and thread id
    prompt_str = "This is a query"
    id = '0'

    # WHEN instantiating the APIDataHandler, a prompt is provided and thread id
    handler = APIDataHandler(APIHandler, PromptHandler)
    handler.api_handler.workstream = "embed"
    handler.api_handler.model = handler.api_handler.config.get("gpt_embedding_params.model")

    # WHEN the api is called
    handler.api_handler.api_call(prompt_str, id)

    # THEN there's response data and latency information
    assert handler.api_handler.response is not None
    assert handler.api_handler.api_latency is not None


def test_successful_api_call_generate():
    # GIVEN a prompt string and thread id
    prompt_str = "This is a query"
    id = '0'

    # WHEN instantiating the APIDataHandler
    handler = APIDataHandler(APIHandler, PromptHandler)
    handler.api_handler.workstream = "generate"

    handler.api_handler.model = "model"
    handler.api_handler.temperature = 0
    handler.api_handler.max_tokens = 0
    handler.api_handler.top_p = 0
    handler.api_handler.frequency_penalty = 0
    handler.api_handler.presence_penalty = 0

    # WHEN calling the api end-point
    with patch.object(handler.api_handler.openai_binding.Completion, 'create', Mock()):
        with patch.object(handler.api_handler, 'logger', MagicMock(spec_set=Logger)):
            handler.api_handler.openai_binding.Completion.create.return_value = MagicMock()
            handler.api_handler.api_call(prompt_str, id)

        # THEN the response and latency data is set in the handler
        print("Asserting that mock object was called once...")
        handler.openai_binding.Completion.create.assert_called_once()
        assert handler.api_handler.response is not None
        assert handler.api_handler.api_latency is not None


def test_valid_params_api_call_generate():
    # GIVEN a prompt string and thread id
    prompt_str = "This is a query"
    id = '0'

    # WHEN instantiating the APIDataHandler and setting the workstream
    handler = APIDataHandler(APIHandler, PromptHandler)
    handler.api_handler.workstream = "generate"

    # AND the request is parameterised based on the config
    handler.api_handler.model = handler.api_handler.config.get("gpt_generate_params.model")
    handler.api_handler.temperature = handler.api_handler.config.get("gpt_generate_params.temperature")
    handler.api_handler.max_tokens = handler.api_handler.config.get("gpt_generate_params.max_tokens")
    handler.api_handler.top_p = handler.api_handler.config.get("gpt_generate_params.top_p")
    handler.api_handler.frequency_penalty = handler.api_handler.config.get("gpt_generate_params.frequency_penalty")
    handler.api_handler.presence_penalty = handler.api_handler.config.get("gpt_generate_params.presence_penalty")

    # AND the api is called
    handler.api_handler.api_call(prompt_str, id)

    # THEN the response and latency data is set in the handler
    assert handler.api_handler.response is not None
    assert handler.api_handler.api_latency is not None



def test_unsuccessful_api_call_embed():
    # GIVEN a prompt string and thread id
    prompt_str = "This is a query"
    id = '0'

    # WHEN instantiating the APIDataHandler but unknow model param is provided
    handler = APIDataHandler(APIHandler, PromptHandler)
    handler.api_handler.workstream = "embed"
    handler.api_handler.model = "gpt-4.3.3"

    # THEN raise an error
    with pytest.raises(openai.error.InvalidRequestError):
        handler.api_handler.api_call(prompt_str, id)


def test_unsuccessful_api_call_generate():
    # GIVEN a prompt string and thread id
    prompt_str = "This is a query"
    id = '0'

    # WHEN instantiating the APIDataHandler and setting the workstream
    handler = APIDataHandler(APIHandler, PromptHandler)
    handler.api_handler.workstream = "generate"

    handler.api_handler.model = "gpt-4.5.5"
    handler.api_handler.temperature = handler.api_handler.config.get("gpt_generate_params.temperature")
    handler.api_handler.max_tokens = handler.api_handler.config.get("gpt_generate_params.max_tokens")
    handler.api_handler.top_p = handler.api_handler.config.get("gpt_generate_params.top_p")
    handler.api_handler.frequency_penalty = handler.api_handler.config.get("gpt_generate_params.frequency_penalty")
    handler.api_handler.presence_penalty = handler.api_handler.config.get("gpt_generate_params.presence_penalty")

    # THEN raise an InvalidRequestError   
    with pytest.raises(openai.error.InvalidRequestError):
        handler.api_handler.api_call(prompt_str, id)