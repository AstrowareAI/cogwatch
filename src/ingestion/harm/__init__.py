"""
Harm/Misalignment Data Collectors Module
Contains separate data collectors for SpiralBench and AI Incident Database
"""

from .spiralbench_data_collector import SpiralBenchDataCollector
from .incidentdb_sync import IncidentDBSync
from .harm_data_collector import HarmDataCollector

# Keep old names as aliases for backward compatibility
SpiralBenchScraper = SpiralBenchDataCollector
HarmScraper = HarmDataCollector

__all__ = ['SpiralBenchDataCollector', 'IncidentDBSync', 'HarmDataCollector', 'SpiralBenchScraper', 'HarmScraper']

