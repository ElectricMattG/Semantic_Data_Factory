from queue import Queue
from unittest.mock import MagicMock, patch
from src.main import Worker, job_manager
from src.api_data_handler.api_data_handler import APIDataHandler


def test_worker_run():
    # GIVEN a worker thread, a prompt to process and an APIDataHandler instance
    prompt = "Test prompt"
    api_data_handler = MagicMock()
    api_data_handler.config.get.return_value = 2  # save after 2 calls

    # WHEN the worker processes the prompt
    queue = Queue()
    worker = Worker(queue, thread_id=1)
    worker.daemon = True
    worker.start()
    queue.put((prompt, api_data_handler))
    queue.join()
    worker.stop()

    # THEN the prompt should be processed and the queue should be empty (see config.py > app.save_after_calls)
    assert api_data_handler.parse_response.call_count == 1
    assert api_data_handler.save_data.call_count == 0  # Not enough calls for saving
    assert queue.qsize() == 0


def test_job_manager(monkeypatch):
    # GIVEN a list of prompts to process and an APIDataHandler instance
    prompts = [" revent 80 cfm", "!awnmower tires without rims", "!qscreen fence without holes"]
    api_data_handler = MagicMock()
    api_data_handler.config.get.return_value = 2  # save after 2 calls
    api_data_handler.prompt_handler.prompts = prompts
    api_data_handler.batches_failed = False

    # WHEN the job manager processes the prompts
    batches_proc_mock = MagicMock()
    with patch("src.main.batches_proc", batches_proc_mock):
        with patch("src.main.time.time", return_value=0):
            job_manager()

    # THEN the prompts should be processed in batches
    assert batches_proc_mock.call_count == 1
    args, kwargs = batches_proc_mock.call_args
    assert len(args) == 2
    assert type(args[0]) == list
    assert args[1] == APIDataHandler()
    assert kwargs == {}

    # AND the APIDataHandler should save the data only after x calls (see config.py > app.save_after_calls)
    assert api_data_handler.save_data.call_count == 0

    # AND if some prompts failed, the job manager should retry them
    api_data_handler.batches_failed = True
    api_data_handler.failed_requests_data = Queue()
    api_data_handler.config.get.return_value = 1  # save after 1 call
    batches_proc_mock.reset_mock()
    with patch("src.main.batches_proc", batches_proc_mock):
        with patch("src.main.time.time", return_value=1):
            job_manager()

    # THEN the failed prompts should be retried
    assert batches_proc_mock.call_count == 1
    args, kwargs = batches_proc_mock.call_args
    assert len(args) == 2
    assert type(args[0]) == list
    assert args[1] == APIDataHandler()
    assert kwargs == {}
