"""
Module for handling API data, including writing to file, saving data, and
parsing api responses.
"""
import json
import os
from dataclasses import dataclass
from statistics import mean, stdev
from queue import Queue
from src.api_base_config.api_base_config import BaseAPIDataHandler
from src.prompt_builder.prompt_builder import PromptHandler
from src.api_handler.api_handler import APIHandler
from src.errors import UnresolvedTransientError, InvalidJSONError


@dataclass
class APIDataHandler(BaseAPIDataHandler):
    """
    The APIDataHandler forms the main public interface for the application.

    The APIDataHandler implements key utilities to handle the API request-response
    data, to ensure reliable robust data transfer between the application and its
    integrations—in this repo storage integrations are stubbed as FILE I/Os, while
    the OpenAI integration is implemented via JSON/HTTPS. Stubbed FILE I/Os can
    be extended for Google Cloud Storage, Big-Query, Kafka, as well as Databricks
    integrations. The class inherits from BaseAPIDataHandler.
    """

    def __init__(
        self,
        api_handler=APIHandler,
        prompt_handler=PromptHandler,
    ) -> None:
        """Constructor for the APIDataHandler class.

        Args:
            api_handler: An APIHandler object.
            prompt_handler: A PromptHandler object.
        """
        super().__init__()
        self.api_handler = api_handler()
        self.prompt_handler = prompt_handler()
        self.query_counter = 0
        self.errors = (
            UnresolvedTransientError,
            self.openai_binding.error.APIConnectionError,
            self.openai_binding.error.APIError,
            self.openai_binding.error.AuthenticationError,
            self.openai_binding.error.InvalidAPIType,
            self.openai_binding.error.InvalidRequestError,
            self.openai_binding.error.OpenAIError,
            self.openai_binding.error.PermissionError,
            self.openai_binding.error.ServiceUnavailableError,
            self.openai_binding.error.SignatureVerificationError,
            self.openai_binding.error.RateLimitError,
            self.openai_binding.error.Timeout,
            self.openai_binding.error.TryAgain,
        )

    def _write_big_query(self):
        # TODO write results back to big query
        pass

    def _get_big_query(self):
        # TODO get queries big query
        pass

    def write_to_file(self, filename: str, data: Queue) -> None:
        """Write the data in the given Queue object to a file.

        Args:
            filename: A string representing the name of the file to be written.
            data: A Queue object containing the data to be written to the file.
        """
        save_buffer = []
        while not data.empty():
            save_buffer.append(data.get())
        with open(filename, "w") as outfile:
            json.dump(save_buffer, outfile, indent=4)

    def save_data(self, id: str) -> None:
        """Save the data to a file.

        Args:
            id: A string representing the id of the thread.
        """
        file_format = self.config.get("output_data.results_format")

        file_str = self.config.get("output_data.results_full_filepath")
        file_str = file_str + str(self.query_counter) + file_format

        if not self.results.empty():
            self.logger.debug("Thread: " + id + " - " + "Writing results to file")
            self.write_to_file(file_str, self.results)  # NOTE flushes buffer
        else:
            self.logger.debug("Thread: " + id + " - " + "The results buffer is empty.")

        file_str = self.config.get("api_performance_data.performance_data_fullpath")
        file_str = file_str + str(self.query_counter) + file_format

        if not self.latencies.empty():
            self.logger.debug("Thread: " + id + " - " + "Writing latency data to file")
            self.write_to_file(file_str, self.latencies)  # NOTE flushes buffer
        else:
            self.logger.debug("Thread: " + id + " - " + "The latency buffer is empty.")

    def check_job_completed(self, id: str) -> bool:
        """Check if the job has been completed.

        Args:
            id: A string representing the id of the thread.

        Returns:
            A boolean indicating whether the job has been completed.
        """
        if self.batches_failed is True:
            self.logger.debug(
                "Thread: "
                + id
                + " - "
                + "There are still prompts that weren't processed."
            )
            self.logger.debug(
                "Thread: "
                + id
                + " - "
                + str(self.cnt_batches_failed)
                + " prompt remained unprocessed."
            )
            return False
        else:
            self.logger.debug("Thread: " + id + " - " + "All queries were processed.")
            return True

    def summary_stats(self, id: str, latency: str) -> None:
        """Calculate and log the summary statistics for the API.

        Args:
            id: A string representing the id of the thread.
            latency: A string representing the latency of the API.
        """
        try:
            api_performance = self._parse_api_performance()

            if api_performance["total_calls"] > 0:
                summary = [
                    "Thread: "
                    + id
                    + " - "
                    + "The cronjob took this long to run "
                    + latency
                    + " seconds",
                    "Thread: "
                    + id
                    + " - "
                    + "The API was successfully called "
                    + str(api_performance["total_calls"])
                    + " times",
                    "Thread: "
                    + id
                    + " - "
                    + "The total number of token processed was "
                    + str(api_performance["total_tokens"]),
                    "Thread: "
                    + id
                    + " - "
                    + "The average latency was "
                    + str(api_performance["mn_latency"])
                    + " seconds",
                    "Thread: "
                    + id
                    + " - "
                    + "The standard deviation was "
                    + str(api_performance["std_latency"])
                    + " seconds",
                    "Thread: "
                    + id
                    + " - "
                    + "The estimated cost in USD was $"
                    + str(api_performance["est_cost"]),
                ]
                for msg in summary:
                    self.logger.info(msg)
            else:
                summary = [
                    "Thread: "
                    + id
                    + " - "
                    + "No data was processed: check your config and network."
                ]
                for msg in summary:
                    self.logger.info(msg)

        except Exception as e:
            self.logger.error(e)

    def parse_response(self, prompt_str: str) -> None:
        """Parse the response from the API.

        Args:
            prompt_str: A string representing the prompt for the API.
        """
        if self.workstream == "generate":
            try:
                response = self.api_handler.response.choices[0]
                self._set_results(json.loads(response.text.strip()))
                latency_dat = self.api_handler.api_latency
                self._set_latency(latency_dat)
            except ValueError:
                raise InvalidJSONError("Invalid JSON in OpenAI response")
        elif self.workstream == "embed":
            try:
                response = self.api_handler.response
                response["prompt_str"] = prompt_str
                self._set_results(json.loads(str(response)))
                latency_dat = self.api_handler.api_latency
                self._set_latency(latency_dat)
            except ValueError:
                raise InvalidJSONError("Invalid JSON in OpenAI response")

    def _parse_api_performance(self) -> dict:
        """Parses API performance data from JSON files and
        compute summary statistics.
        """

        latency = []
        token_cnt = []
        est_cost = []
        api_data_dir = "/".join(
            self.config.get("api_performance_data.performance_data_fullpath").split(
                "/"
            )[:-1]
        )
        api_data_files = os.listdir(api_data_dir)

        for data_file in api_data_files:
            file_str = api_data_dir + "/" + data_file

            try:
                with open(file_str, "r") as data_file:
                    dat = json.loads(data_file.read())
                latency.append([dt["latency"] for dt in dat])
                token_cnt.append([dt["token_total"] for dt in dat])
                est_cost.append([dt["estimated_cost_US"] for dt in dat])
            except ValueError:
                self.logger.warning("Thread: Main - Invalid JSON when summarising job")
                continue

        if len(sum(latency, [])) > 0:
            total_calls = len(sum(latency, []))
            mean_latency = mean(sum(latency, []))
            stdev_latency = stdev(sum(latency, []))
            total_tokens = sum(sum(token_cnt, []))
            est_cost = sum(sum(est_cost, []))

            return {
                "total_calls": total_calls,
                "mn_latency": mean_latency,
                "std_latency": stdev_latency,
                "total_tokens": total_tokens,
                "est_cost": est_cost,
            }
        else:
            return {
                "total_calls": 0,
                "mn_latency": 0,
                "std_latency": 0,
                "total_tokens": 0,
                "est_cost": 0,
            }
