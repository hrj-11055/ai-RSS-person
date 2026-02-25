"""
Publishers package for AI-RSS-PERSON project.

This package provides different publishing strategies for reports.
"""

from .cloud_publisher import CloudPublisher
from .local_publisher import LocalPublisher

__all__ = [
    "CloudPublisher",
    "LocalPublisher",
]
