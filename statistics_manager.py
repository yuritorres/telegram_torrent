"""Backward-compatibility shim – use src.services.StatisticsManager directly."""
from src.services.statistics_service import StatisticsManager

__all__ = ["StatisticsManager"]
