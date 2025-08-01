import os
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .analysis_processor import AnalysisProcessor
from ..utils.check_utils import CheckUtils


class ConfirmationProcessor:
    """Vulnerability confirmation processor responsible for executing multi-threaded vulnerability confirmation checks"""
    
    def __init__(self, analysis_processor: AnalysisProcessor):
        self.analysis_processor = analysis_processor
    
    def execute_vulnerability_confirmation(self, task_manager):
        """Execute vulnerability confirmation checks"""
        tasks = task_manager.get_task_list()
        if len(tasks) == 0:
            return []

        # Define number of threads in thread pool, get from env
        max_threads = int(os.getenv("MAX_THREADS_OF_CONFIRMATION", 5))
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [
                executor.submit(self._process_single_task_check, task, task_manager) 
                for task in tasks
            ]

            with tqdm(total=len(tasks), desc="Checking vulnerabilities") as pbar:
                for future in as_completed(futures):
                    future.result()  # Wait for each task to complete
                    pbar.update(1)  # Update progress bar

        return tasks
    
    def _process_single_task_check(self, task, task_manager):
        """Process vulnerability check for a single task"""
        print("\n" + "="*80)
        print(f"🔍 Starting to process task ID: {task.id}")
        print("="*80)
        
        # Check if task is already processed
        if CheckUtils.is_task_already_processed(task):
            print("\n🔄 This task has been processed, skipping...")
            return
        
        # Delegate to analysis processor for specific analysis work
        self.analysis_processor.process_task_analysis(task, task_manager) 