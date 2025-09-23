#!/usr/bin/env python3
"""
os_lab_assignment2.py
Implements Lab Assignment 2 requirements:
- logging to a file with timestamps and process names
- a simulated process task
- create at least two processes using multiprocessing
- start, join, and ensure termination
Generates: process_log.txt
"""

import multiprocessing
import logging
import time
import random
import sys
from datetime import datetime

LOG_FILE = "process_log.txt"

def init_logging():
    """
    Initialize logging to file and console.
    Log format includes timestamp, process name, PID, level and message.
    """
    fmt = "%(asctime)s [%(processName)s|PID:%(process)d] %(levelname)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(LOG_FILE, mode="w"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def system_process(task_name: str, work_seconds: float = None):
    """
    Simulated process task.
    - Logs start and end messages.
    - Sleeps for 'work_seconds' to simulate CPU/I/O work.
    - If work_seconds is None, pick a small random value to diversify logs.
    """
    try:
        if work_seconds is None:
            # randomized duration to simulate different burst times
            work_seconds = round(random.uniform(1.0, 3.0), 2)

        logging.info(f"{task_name} started. Simulated work: {work_seconds}s")
        # Simulate work (blocking sleep represents I/O or CPU work for this lab)
        time.sleep(work_seconds)
        logging.info(f"{task_name} completed.")
    except Exception as e:
        logging.exception(f"{task_name} crashed with exception: {e}")

def create_and_run_processes(process_count=2):
    """
    Create 'process_count' processes and run them concurrently.
    Demonstrates process creation, start, join, and termination.
    """
    procs = []
    for i in range(process_count):
        name = f"Process-{i+1}"
        # Pass a slightly different work time for each process (optional)
        p = multiprocessing.Process(
            target=system_process,
            name=name,
            args=(name,)  # only task_name; duration randomized in system_process
        )
        procs.append(p)

    logging.info(f"Spawning {len(procs)} processes.")
    for p in procs:
        p.start()
        logging.info(f"Started {p.name} (PID {p.pid})")

    # Wait for all processes to finish
    for p in procs:
        p.join(timeout=10)  # timeout protects against indefinite hang in teaching labs
        if p.is_alive():
            logging.warning(f"{p.name} (PID {p.pid}) did not exit in time. Terminating.")
            p.terminate()
            p.join()
        logging.info(f"{p.name} (PID {p.pid}) has exited. Exit code: {p.exitcode}")

if __name__ == "__main__":
    # Initialize logging first so child processes inherit config when they log.
    # Note: multiprocessing on some platforms (Windows) launches fresh Python interpreters.
    init_logging()
    logging.info("Lab Assignment 2 - System Starting")

    # Example: create at least two processes as required by assignment.
    # You can change the count or spawn processes with different targets for extensions.
    create_and_run_processes(process_count=2)

    logging.info("Lab Assignment 2 - System Shutdown")
    # Optionally print a short summary of the generated log file location
    logging.info(f"Execution log written to {LOG_FILE}")
