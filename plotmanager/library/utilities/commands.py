import os
import pathlib
import psutil
import sys
import time

from datetime import datetime, timedelta

from plotmanager.library.parse.configuration import get_config_info
from plotmanager.library.utilities.exceptions import ManagerError, TerminationException
from plotmanager.library.utilities.jobs import load_jobs
from plotmanager.library.utilities.log import check_log_progress
from plotmanager.library.utilities.print import print_table
from plotmanager.library.utilities.processes import get_manager_processes, get_running_plots, start_process


def start_manager():
    if get_manager_processes():
        raise ManagerError('Manger is already running.')

    directory = pathlib.Path().resolve()
    stateless_manager_path = os.path.join(directory, 'stateless-manager.py')
    if not os.path.exists(stateless_manager_path):
        raise FileNotFoundError('Failed to find stateless-manager.')
    manager_log_file_path = os.path.join(directory, 'manager.log')
    manager_log_file = open(manager_log_file_path, 'a')
    python_file_path = sys.executable
    pythonw_file_path = '\\'.join(python_file_path.split('\\')[:-1] + ['pythonw.exe'])
    if os.path.exists(pythonw_file_path):
        python_file_path = pythonw_file_path
    args = [python_file_path, stateless_manager_path]
    start_process(args=args, log_file=manager_log_file)
    time.sleep(3)
    if not get_manager_processes():
        raise ManagerError('Failed to start Manager.')
    print('Manager has started...')


def stop_manager():
    processes = get_manager_processes()
    if not processes:
        print("No manager processes were found.")
        return
    for process in processes:
        try:
            process.terminate()
        except psutil.NoSuchProcess:
            pass
    if get_manager_processes():
        raise TerminationException("Failed to stop manager processes.")
    print("Successfully stopped manager processes.")


def view():
    chia_location, log_directory, config_jobs, log_check_seconds, max_concurrent = get_config_info()
    while True:
        try:
            jobs = load_jobs(config_jobs)
            running_work = {}
            jobs, running_work = get_running_plots(jobs, running_work)
            check_log_progress(jobs=jobs, running_work=running_work)
            print_table(jobs, running_work, datetime.now() + timedelta(seconds=60), False)
            time.sleep(60)
        except KeyboardInterrupt:
            print("Stopped view.")
            exit()
