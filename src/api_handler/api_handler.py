"""
This module implement the APIHandler for making calls to OpenAIs
API.
"""
import time
from abc import ABC, abstractmethod
from src.api_base_config.api_base_config import BaseAPIDataHandler
import random
from src.errors import UnresolvedTransientError


class ABCAPIHandler(ABC):
    """
    Base class for APIHandler.
    """

    def __init__(self):
        """
        Constructor method of APIHandler
        """
        super().__init__()
        self.final_prompt: str
        self.model: str
        self.temperature: int
        self.max_tokens: int
        self.top_p: int
        self.frequency_penalty: int
        self.presence_penalty: int

    @abstractmethod
    def hello_gpt(self):
        raise NotImplementedError("Subclass and implement.")


class APIHandler(ABCAPIHandler, BaseAPIDataHandler):
    """
    Handles the calls to OpenAI's API.

    The APIHandler handles the calls to OpenAI’s server, implements error handling
    for transient APIErrors.
    """

    def __init__(self, final_prompt="") -> None:
        super().__init__()
        """
        Constructor method for APIHandler.
        """
        self.final_prompt = final_prompt
        if self.workstream == "generate":
            self.model = self.config.get("gpt_generate_params.model")
            self.temperature = self.config.get("gpt_generate_params.temperature")
            self.max_tokens = self.config.get("gpt_generate_params.max_tokens")
            self.top_p = self.config.get("gpt_generate_params.top_p")
            self.frequency_penalty = self.config.get(
                "gpt_generate_params.frequency_penalty"
            )
            self.presence_penalty = self.config.get(
                "gpt_generate_params.presence_penalty"
            )
        elif self.workstream == "embed":
            self.model = self.config.get("gpt_embedding_params.model")

        self.response = None
        self.api_latency = None
        self._transient_errors = (
            self.openai_binding.error.Timeout,
            self.openai_binding.error.APIError,
            self.openai_binding.error.RateLimitError,
        )

    def api_call(self, prompt_str, id: int) -> None:
        """This function handles the API call, retry logic and logging.

        Args:
            prompt_str: string passed to OpenAI's api
            id: thread id of the worker making the call
        """
        openai_binding = self.openai_binding
        api_call_time = time.time()

        if self.workstream == "generate":
            # raise self.api_data_handler.openai_binding.error.APIConnectionError
            start_time = time.time()
            response = openai_binding.Completion.create(
                model=self.model,
                prompt=prompt_str,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
            )
            end_time = time.time()
        elif self.workstream == "embed":
            # raise self.openai_binding.error.APIConnectionError
            start_time = time.time()
            response = openai_binding.Embedding.create(
                input=prompt_str, model=self.model
            )
            end_time = time.time()
        latency = end_time - start_time
        self.response = response

        if self.workstream == "generate":
            token_cnt_prompt = self.response.usage.prompt_tokens
            token_cnt_resp = self.response.usage.completion_tokens
            token_cnt_total = self.response.usage.total_tokens
            token_cost_1000 = self.config.get("gpt_generate_params.token_cost_1000")
            self.api_latency = {
                "call_time": time.ctime(api_call_time),
                "latency": latency,
                "tokens_prompt": token_cnt_prompt,
                "tokens_response": token_cnt_resp,
                "token_total": token_cnt_total,
                "token_cost_1000_US": token_cost_1000,
                "estimated_cost_US": (token_cnt_total / 1000) * token_cost_1000,
            }

        elif self.workstream == "embed":
            token_cnt_prompt = self.response.usage.prompt_tokens
            token_cnt_total = self.response.usage.total_tokens
            token_cost_1000 = self.config.get(
                "gpt_embedding_params.token_cost_1000"
            )  # We need the embedding config
            self.api_latency = {
                "call_time": time.ctime(api_call_time),
                "latency": latency,
                "tokens_prompt": token_cnt_prompt,
                "token_total": token_cnt_total,
                "token_cost_1000_US": token_cost_1000,
                "estimated_cost_US": (token_cnt_total / 1000) * token_cost_1000,
            }

        self.logger.debug(
            "Thread: " + id + " - " + "These are the details: %s",
            self.api_latency.__str__(),
        )

    def hello_gpt(self, prompt_str, id) -> None:
        """This function handles the API call, retry logic and logging.

        Args:
            prompt_str: string passed to OpenAI's api
            id: thread id of the worker making the call
        """
        if self.workstream == "generate":
            params = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "frequency_penalty": self.frequency_penalty,
                "presence_penalty": self.presence_penalty,
            }
        elif self.workstream == "embed":
            params = {
                "model": self.model,
            }

        self.logger.debug(
            "Thread: " + id + " - " + "Making a call to gpt: %s", params.__str__()
        )
        for retry in range(self.config.get("exponential_backoff.max_retries")):
            try:  # NOTE make a call. handle transients.
                self.api_call(prompt_str, id)
                break
            except self._transient_errors as e:
                self.logger.warning(
                    "Thread: "
                    + id
                    + " - "
                    + f"OpenAI API encountered a transient error: {e.__class__.__name__}. Retrying api call..."
                )
                self.logger.debug(
                    "Thread: " + id + " - " + "Retry our call to gpt: %s",
                    params.__str__(),
                )
                time.sleep(self._jitter(retry))
        else:
            self.logger.warning(
                "Thread: " + id + " - " + "Max retries reached, API request failed"
            )
            raise UnresolvedTransientError

    def _jitter(self, retry: int) -> float:
        """Calculated the sleep time for exponential backoff

        Args:
            retry (int): the count of the current retry

        Returns:
            jittered sleep time (seconds)
        """
        base_sleep_time = self.config.get("exponential_backoff.base_sleep_time")
        max_sleep_time = self.config.get("exponential_backoff.max_sleep_time")
        retry = random.randint(0, 3)
        sleep_time = min(base_sleep_time * (2**retry), max_sleep_time)
        return sleep_time * random.uniform(
            self.config.get("exponential_backoff.rand_low"),
            self.config.get("exponential_backoff.rand_hi"),
        )
