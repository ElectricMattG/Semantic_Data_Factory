"""
A module that implements the PromptHandler.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from src.api_base_config.api_base_config import BaseAPIDataHandler
from src.errors import InvalidConfig

class ABCPrompt(ABC):
    """
    Abstract baseclass for the prompt-builder component.
    """

    def __init__(self):
        super().__init__()
        self.query_data: pd.DataFrame
        self.prompts: list  # NOTE each prompt holds a batch
        self.queries_batched: list
        self.approx_batch_size: int

    @abstractmethod
    def batch_queries(self):
        raise NotImplementedError("Subclass and implement.")

    @abstractmethod
    def next(self):
        raise NotImplementedError("Subclass and implement.")


class PromptHandler(ABCPrompt, BaseAPIDataHandler):
    """
    The PromptHandler handles the input data for synthetic data generation and
    for embeddings. The main function is to provide an interface for the
    application-data with the query-data, but the handler also enables a
    prompt-injection framework, so one can also get embeddings for more complex
    prompt structures, i.e. involving multiple products, or product-customer
    interactions.
    """

    def __init__(self) -> None:
        """
        Constructor method for prompt handler
        """
        super().__init__()
        self.query_data = pd.read_csv(self.config.get("input_data.query_full_filepath"))
        self.approx_batch_size = 15
        self.prompts = []
        self.queries_batched = []
        self.batch_queries()
        self.build_prompts()

    def batch_queries(self) -> None:
        """Batches the queries so they can be injected into a prompt template."""

        queries = self.query_data["query"].to_numpy()
        self.queries_batched = np.array_split(
            queries, len(queries) / self.approx_batch_size
        )  # attempting to batch about 15 queries TODO fix this

    def build_prompts(self):
        """Build out a prompt by injecting queries into the prompt template."""

        self.logger.info(
            "Thread: Main - Building the prompting template and batching queries..."
        )

        if self.workstream == "generate":
            # 3-tier prompt template
            prompt_start = self.config.get("prompt.start")
            prompt_instruction = self.config.get("prompt.instruction")
            prompt_defs = self.config.get("prompt.def")

            for queries_ in self.queries_batched:
                query = ""
                for text in queries_:
                    query = query + text + ", "

                final_prompt = prompt_start + query + prompt_instruction + prompt_defs
                self.prompts.append(final_prompt)
        elif self.workstream == "embed":
            for queries_ in self.query_data["query"].to_numpy():
                self.prompts.append(str(queries_))
        else:
            self.logger.error(
            "Thread: Main - Workstream not recognised. Check config.py > WORKSTREAM"
            )
            raise InvalidConfig()       

    def next(self):
        pass
