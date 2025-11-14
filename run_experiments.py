"""
Script to run two_agents.py multiple times for parameter tuning experiments
"""

import subprocess
import sys
import time
from datetime import datetime

def run_experiment(run_number, total_runs):
    """Run a single experiment"""
    print("\n" + "="*80)
    print(f"RUNNING EXPERIMENT {run_number} of {total_runs}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    try:
        # Run the two_agents.py script
        result = subprocess.run(
            [sys.executable, "two_agents.py"],
            capture_output=False,
            text=True,
            check=True
        )

        print("\n" + "-"*80)
        print(f"✓ Experiment {run_number} completed successfully")
        print("-"*80)

        return True

    except subprocess.CalledProcessError as e:
        print("\n" + "-"*80)
        print(f"✗ Experiment {run_number} failed with error")
        print(f"Error: {e}")
        print("-"*80)

        return False
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("EXPERIMENT INTERRUPTED BY USER")
        print("="*80)
        raise

def main():
    # Number of times to run the experiment
    NUM_RUNS = 5  # Change this to run more or fewer experiments

    print("\n" + "="*80)
    print("MULTI-RUN EXPERIMENT LAUNCHER")
    print("="*80)
    print(f"Total experiments to run: {NUM_RUNS}")
    print(f"Script to execute: two_agents.py")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    successful_runs = 0
    failed_runs = 0

    try:
        for i in range(1, NUM_RUNS + 1):
            success = run_experiment(i, NUM_RUNS)

            if success:
                successful_runs += 1
            else:
                failed_runs += 1

            # Small delay between runs (optional)
            if i < NUM_RUNS:
                print(f"\nWaiting 2 seconds before next run...\n")
                time.sleep(2)

        # Summary
        print("\n" + "="*80)
        print("ALL EXPERIMENTS COMPLETED")
        print("="*80)
        print(f"Total runs: {NUM_RUNS}")
        print(f"Successful: {successful_runs}")
        print(f"Failed: {failed_runs}")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

    except KeyboardInterrupt:
        print("\n" + "="*80)
        print("EXPERIMENT BATCH INTERRUPTED")
        print("="*80)
        print(f"Completed runs: {successful_runs + failed_runs}")
        print(f"Successful: {successful_runs}")
        print(f"Failed: {failed_runs}")
        print(f"Remaining: {NUM_RUNS - (successful_runs + failed_runs)}")
        print("="*80 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
