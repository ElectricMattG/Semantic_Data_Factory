import pytest
import os
import json
from queue import Queue
from src.api_data_handler.api_data_handler import APIDataHandler
from unittest.mock import MagicMock, patch, Mock

@pytest.fixture
def api_data_handler():
    return APIDataHandler()


def test_write_to_file(api_data_handler):
    # GIVEN a queue
    filename = "test_file.json"
    data = Queue()

    # WHEN data there data on the queues and we write to file
    data.put({"name": "Alice", "age": 25})
    data.put({"name": "Bob", "age": 30})
    api_data_handler.write_to_file(filename, data)

    # THEN the data should be written to file
    with open(filename, "r") as f:
        assert json.load(f) == [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
    os.remove(filename)


def test_save_data(api_data_handler):
    # GIVEN
    id = "test_id"
    api_data_handler.results.put({"name": "Alice", "age": 25})
    api_data_handler.results.put({"name": "Bob", "age": 30})
    api_data_handler.latencies.put(1.2)
    api_data_handler.latencies.put(0.8)
    
    # WHEN saving to file
    with patch.object(api_data_handler, 'write_to_file', Mock()) as write_f:
        api_data_handler.save_data(id)

    # THEN write_to_file has multiple calls
    write_f.assert_called()


# GIVEN a job ran through the queries/prompts
def test_check_job_completed(api_data_handler):
    # WHEN no batches have failed
    api_data_handler.batches_failed = False

    # THEN job has completed
    assert api_data_handler.check_job_completed("Main") is True


# GIVEN a job ran through the queries/prompts
def test_check_job_not_completed(api_data_handler):
    # WHEN job has not completed with failed requests
    api_data_handler.batches_failed = True

    # THEN job hasn't completed
    assert api_data_handler.check_job_completed("Main") is False


def test_summary_stats(api_data_handler, caplog):
    # GIVEN  there is no data on the queues
    id = "Main"
    api_data_handler.latencies = Queue()
    api_data_handler.failed_requests_data = Queue()

    # WHEN the job is summarised
    api_data_handler.summary_stats(id, 0)
    
    # THEN summary stats should produce a log message like this
    expected_logs = [
        "Thread: Main - No data was processed: check your config and network."
    ]
    for expected_log in expected_logs:
        assert expected_log in caplog.text
