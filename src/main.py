"""
This module contains the implementation of the `Worker` class and the `job_manager`
function. The job_manager() function is the entry point for the application.
"""
from src.api_data_handler.api_data_handler import APIDataHandler
from src.prompt_builder.prompt_builder import PromptHandler
from src.api_handler.api_handler import APIHandler
from threading import Thread, Event
from queue import Queue
import time


class Worker(Thread):
    """
    Represents a worker thread that processes prompts from the queue.
    """

    def __init__(self, queue: Queue, thread_id: int) -> None:
        """
        Initializes a new instance of the Worker Thread.

        Args:
            queue: A queue of prompts to be processed.
            thread_id: An integer representing the thread ID.
        """
        Thread.__init__(self)
        self.queue = queue
        self.thread_id = thread_id
        self._stop_event = Event()

    def run(self):
        """Overrides the run() method of the Thread class. Processes the prompts
        from the queue, handles errors and saves data.
        """
        while not self._stop_event.is_set():
            # Get the work from the queue and expand the tuple
            id = str(self.thread_id)

            try:
                final_prompt, handler = self.queue.get()
                save_after = handler.config.get("app.save_after_calls")
                handler.logger.debug("Thread: " + id + " - " + final_prompt)
                try:
                    handler.api_handler.hello_gpt(final_prompt, id)
                    handler.parse_response(final_prompt)
                    handler.query_counter += 1

                    if (handler.query_counter % save_after) == 0:
                        handler.save_data(id)

                except handler.errors as e:  # NOTE if not transient, handle error
                    error = e.__class__.__name__
                    handler.logger.error(
                        "Thread: "
                        + id
                        + " - "
                        + f"The APIHandler returned an error: {error}. Storing unprocessed prompt. Will try again later..."
                    )
                    handler.query_counter += 1
                    handler._set_failed_requests_data(final_prompt)
                    if (handler.query_counter % save_after) == 0:
                        handler.save_data(id)

                except (
                    Exception
                ) as e:  # NOTE catch other errors that are not native to OpenAI
                    error = e.__class__.__name__
                    handler.logger.error(
                        "Thread: "
                        + id
                        + " - "
                        + f"The APIHandler returned an error: {error}. Storing unprocessed prompt. Will try again later..."
                    )
                    handler.query_counter += 1
                    handler._set_failed_requests_data(final_prompt)
                    if (handler.query_counter % save_after) == 0:
                        handler.save_data(id)
            finally:
                self.queue.task_done()

    def stop(self):
        self._stop_event.set()


def batches_proc(prompts_to_process: list, handler: APIDataHandler) -> None:
    """Processes a batch of prompts using multithreading.

    Args:
        prompts_to_process: A list of prompts to be processed.
        handler: a handle to the instance of the APIDataHandler.
    """
    tasks = Queue()
    for i in range(handler.config.get("app.concur_workers")):
        worker = Worker(tasks, thread_id=i)
        worker.daemon = True
        worker.start()
    if handler.config.get("app.max_recs") > 0:
        max_recs = handler.config.get(
            "app.max_recs"
        )  # NOTE queries count is available
    elif handler.config.get("app.max_recs") == 0:
        max_recs = len(prompts_to_process)
    for final_prompt in prompts_to_process[0:max_recs]:
        tasks.put((final_prompt, handler))
    tasks.join()


def job_manager() -> None:
    """
    This function manages the processing of prompts in a multi-threaded environment.
    The job manager interfaces with the application’s public API interface and manages
    the multithreading logic and queues for the application.
    """

    # instantiate the APIDataHandler - Dependency Injection
    start_time = time.time()
    handler = APIDataHandler(APIHandler, PromptHandler)
    handler.logger.info(
        "Thread: Main - Connecting to OpenAI and processing the prompts..."
    )
    batches_proc(handler.prompt_handler.prompts, handler)
    handler.save_data("Main")  # NOTE save data and flush buffers for rettry

    # NOTE this is a rety on prompts that were not processed
    max_retries = handler.config.get("app.max_retries")
    retries = 0  # NOTE start see config for parameters
    handler.check_job_completed("Main")
    while (handler.batches_failed is True) & (retries < max_retries):
        handler.logger.info("Thread: Main - Retrying failed requests...")
        failed_requests_data = []
        queue_to_proc = handler.failed_requests_data
        while not queue_to_proc.empty():
            failed_requests_data.append(
                queue_to_proc.get()
            )  # NOTE get queued results FIFO, clear the queue
        handler.cnt_batches_failed = 0
        handler.batches_failed = False

        batches_proc(failed_requests_data, handler)
        handler.save_data("Main")
        retries += 1

    end_time = time.time()
    handler.summary_stats(id="Main", latency=str(end_time - start_time))
    file_str = handler.config.get("output_data.unprocessed_prompts")
    buffer_save = handler.failed_requests_data
    if not buffer_save.empty():
        handler.logger.info("Thread: Main - There are unprocessed prompts...")
        handler.logger.debug(
            "Thread: Main - Writing failed results to file after retries..."
        )
        handler.write_to_file(file_str, buffer_save)  # NOTE flushes buffer


if __name__ == "__main__":
    job_manager()
