"""
This module provides base config for all system components.
"""
from dataclasses import dataclass
from pyconfs import Configuration
from src.config import defaults
import logging
from typing import Optional
import openai
import sys
from queue import Queue


class CustomConf(Configuration):
    """
    A custom configuration class that inherits from pyconfs Configuration class.
    """

    @staticmethod
    def init_logger(self, name: str, log_lib: logging) -> Optional[None]:
        """Initialize a logger with the logging configuration defined in the
        configuration dictionary.

        Args:
            name: The name of the logger.
            log_lib: The logging library to use.
        """
        root_logger = log_lib.getLogger(name)
        root_logger.handlers = []

        root_handler = logging.StreamHandler(stream=sys.stdout)
        root_handler.setFormatter(
            logging.Formatter(fmt=self.config.get("logging.format"))
        )
        root_logger.addHandler(root_handler)

        file_handler = logging.FileHandler(self.config.get("logging.output_full_path"))
        file_handler.setFormatter(
            logging.Formatter(fmt=self.config.get("logging.format"))
        )
        root_logger.addHandler(file_handler)

        root_logger.setLevel(self.config.get("logging.level"))
        return root_logger

    def get(self, key: str) -> Optional[None]:
        """Get the value corresponding to the given key string.

        Args:
            key (str): A string in the form "first_level_key.second_level_key".
        """
        return self.data[key.split(".")[0]][key.split(".")[1]]


# NOTE this dataclass definition
@dataclass
class BaseAPIDataHandler:
    """
    A base class for all components. It makes common assets available
    at run-time: configuation, logger, OpenAI python bindings, Queues,
    counters, and checks. The workstream is also set with the necessary
    components creating a "workstream aware" architecture.
    """

    def __init__(self) -> None:
        """Initialize a BaseAPIDataHandler instance."""
        self.openai_binding = openai
        self.config = CustomConf(name=self.__class__.__name__).from_dict(defaults)
        self.openai_binding.api_key = self.config.get("account.api_key")
        self.logger = CustomConf.init_logger(
            self, name=self.__class__.__name__, log_lib=logging
        )  # TODO set the handlers
        # TODO change the implementation of lists to queues set max-length to max_queue till save
        self.latencies: Queue = Queue()  # NOTE queue is infinite
        self.results: Queue = Queue()
        self.failed_requests_data: Queue = Queue()
        self.job_description: dict = {}
        self.batches_failed = False
        self.query_counter: int = 0
        self.cnt_batches_failed: int = 0
        self.workstream: str = self.config.get("app.workstream")

    def _set_latency(self, latency_dat: tuple) -> None:
        """Set the latency data in the latencies queue.

        Args:
            latency_dat: A tuple containing the latency data.
        """
        self.latencies.put(latency_dat)

    def _set_results(self, json_response: list) -> None:
        """Set the JSON response data in the results queue.

        Args:
            json_response (list): A list containing the JSON response data.
        """
        self.results.put(json_response)

    def _set_failed_requests_data(self, final_prompt: str) -> None:
        """Set the failed requests data in the failed requests queue.

        Args:
            final_prompt (str): The final prompt string.
        """
        self.failed_requests_data.put(final_prompt)
        self.batches_failed = True
        self.cnt_batches_failed += 1
