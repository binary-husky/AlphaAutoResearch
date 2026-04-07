"""
Scan and display running PAI DLC jobs.

Usage:
    python -m rl_auto_research.blueprint_runner.scan_jobs
"""

import time

from rl_auto_research.config import config
from rl_auto_research.pai.client import list_jobs


def main():
    jobs = list_jobs(
        region_id=config["alibaba_cloud"]["region_id"],
        workspace_id=config["alibaba_cloud"]["workspace_id"],
        start_time=time.strftime(
            "%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() - 15 * 24 * 3600)
        ),
        end_time=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
    )

    for job in jobs:
        print(job)


if __name__ == "__main__":
    main()
