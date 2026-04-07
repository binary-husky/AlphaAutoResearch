"""
Abstract base class for experiment launchers.
"""

from abc import ABC, abstractmethod


class ExperimentSubagent(ABC):
    """
    Base class for launching experiments on different backends.

    Subclass this and implement launch(), monitor(), stop().
    """

    @abstractmethod
    def launch(self, blueprint_path: str, exp_name: str, **kwargs) -> str:
        """Launch an experiment. Returns a backend-specific job identifier."""
        ...

    @abstractmethod
    def monitor(self, job_id: str) -> str:
        """Block until the job finishes. Returns terminal status."""
        ...

    @abstractmethod
    def stop(self, job_id: str) -> None:
        """Stop a running job."""
        ...
