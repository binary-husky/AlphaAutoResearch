"""
Alibaba Cloud PAI DLC client.

Handles job creation, listing, monitoring, and dataset creation.
All credentials come from alpha_auto_research.config.
"""

import json
import time

from alibabacloud_tea_openapi.models import Config
from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_pai_dlc20201203.client import Client as DLCClient
from alibabacloud_pai_dlc20201203.models import (
    ListJobsRequest,
    CreateJobRequest,
    GetJobRequest,
    StopJobRequest,
    DeleteJobRequest,
)
from alibabacloud_aiworkspace20210204.client import Client as AIWorkspaceClient
from alibabacloud_aiworkspace20210204.models import CreateDatasetRequest

import os

from alpha_auto_research.config import config


def _set_credentials():
    cloud = config["alibaba_cloud"]
    os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"] = cloud["access_key_id"]
    os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"] = cloud["access_key_secret"]


def _get_dlc_client(region_id: str) -> DLCClient:
    _set_credentials()
    cred = CredClient()
    return DLCClient(
        config=Config(
            credential=cred,
            region_id=region_id,
            endpoint=f"pai-dlc.{region_id}.aliyuncs.com",
        )
    )


def _get_workspace_client(region_id: str) -> AIWorkspaceClient:
    _set_credentials()
    cred = CredClient()
    return AIWorkspaceClient(
        config=Config(
            credential=cred,
            region_id=region_id,
            endpoint=f"aiworkspace.{region_id}.aliyuncs.com",
        )
    )


# ---------------------------------------------------------------------------
# Job operations
# ---------------------------------------------------------------------------

def create_job(
    exp_name: str,
    n_nodes: int,
    priority: int,
    region_id: str,
    workspace_id: int,
    clone_target: str,
    clone_target_time_range: tuple[str, str],
    user_command: str,
) -> str:
    """Clone a template job and launch it with overrides. Returns job_id."""
    client = _get_dlc_client(region_id)

    print("-------- Fetching Job to Clone ----------")
    jobs = client.list_jobs(ListJobsRequest(
        display_name=clone_target,
        workspace_id=workspace_id,
        page_number=1,
        page_size=20,
        start_time=clone_target_time_range[0],
        end_time=clone_target_time_range[1],
    ))

    assert len(jobs.body.jobs) == 1, (
        "Expected exactly 1 template job in the given time range, "
        f"got {len(jobs.body.jobs)}. Adjust clone_target_time_range."
    )
    template = jobs.body.jobs[0]

    print("-------- Creating Job ----------")
    params = template.to_map()
    params["DisplayName"] = str(exp_name)
    params["JobSpecs"][0]["PodCount"] = int(n_nodes)
    params["Priority"] = int(priority)
    params["UserCommand"] = str(user_command)

    resp = client.create_job(CreateJobRequest().from_map(params))
    job_id = resp.body.job_id
    print(f"Created job: {job_id}")
    return job_id


def list_jobs(
    region_id: str,
    workspace_id: int,
    start_time: str,
    end_time: str,
    pages: int = 4,
    page_size: int = 20,
) -> list[dict]:
    """List jobs, deduplicated, across multiple pages."""
    client = _get_dlc_client(region_id)
    seen = set()
    results = []

    for page in range(1, pages + 1):
        jobs = client.list_jobs(ListJobsRequest(
            workspace_id=workspace_id,
            page_number=page,
            page_size=page_size,
            start_time=start_time,
            end_time=end_time,
        ))
        for job in jobs.body.jobs:
            m = job.to_map()
            job_id = m["JobId"]
            if job_id not in seen:
                seen.add(job_id)
                results.append({
                    "job_id": job_id,
                    "display_name": m["DisplayName"],
                    "status": m["Status"],
                    "create_time": m["GmtCreateTime"],
                })

    return results


def stop_job(region_id: str, job_id: str):
    """Stop a running/queuing job."""
    client = _get_dlc_client(region_id)
    client.stop_job(job_id, StopJobRequest())
    print(f"Stopped job: {job_id}")


def delete_job(region_id: str, job_id: str):
    """Delete a job."""
    client = _get_dlc_client(region_id)
    client.delete_job(job_id, DeleteJobRequest())
    print(f"Deleted job: {job_id}")


def wait_for_job(region_id: str, job_id: str, poll_interval: float = 5.0) -> str:
    """Block until job reaches a terminal state. Returns status string."""
    client = _get_dlc_client(region_id)
    while True:
        job = client.get_job(job_id, GetJobRequest()).body
        print(f"job({job_id}) is {job.status}")
        if job.status in ("Succeeded", "Failed", "Stopped"):
            return job.status
        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Dataset operations
# ---------------------------------------------------------------------------

def create_nas_dataset(
    region_id: str, workspace_id: int, name: str,
    nas_id: str, nas_path: str, mount_path: str,
) -> str:
    client = _get_workspace_client(region_id)
    resp = client.create_dataset(CreateDatasetRequest(
        workspace_id=workspace_id,
        name=name,
        data_type="COMMON",
        data_source_type="NAS",
        property="DIRECTORY",
        uri=f"nas://{nas_id}.{region_id}{nas_path}",
        accessibility="PRIVATE",
        source_type="USER",
        options=json.dumps({"mountPath": mount_path}),
    ))
    return resp.body.dataset_id


def create_oss_dataset(
    region_id: str, workspace_id: int, name: str,
    oss_bucket: str, oss_endpoint: str, oss_path: str, mount_path: str,
) -> str:
    client = _get_workspace_client(region_id)
    resp = client.create_dataset(CreateDatasetRequest(
        workspace_id=workspace_id,
        name=name,
        data_type="COMMON",
        data_source_type="OSS",
        property="DIRECTORY",
        uri=f"oss://{oss_bucket}.{oss_endpoint}{oss_path}",
        accessibility="PRIVATE",
        source_type="USER",
        options=json.dumps({"mountPath": mount_path}),
    ))
    return resp.body.dataset_id
