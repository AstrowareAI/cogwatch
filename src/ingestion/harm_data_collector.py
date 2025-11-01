"""
Harm/Misalignment Data Collector for Cogwatch
DEPRECATED: This file is kept for backward compatibility.
Please use src.ingestion.harm.harm_data_collector.HarmDataCollector instead.
"""

# Import from the new modular location
# Handle both relative imports (when used as module) and absolute imports (when run directly)
try:
    from .harm.harm_data_collector import HarmDataCollector
except ImportError:
    # Fallback for direct script execution
    import sys
    import os
    # Add parent directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.ingestion.harm.harm_data_collector import HarmDataCollector

# Export for backward compatibility (keeping old name as alias)
HarmScraper = HarmDataCollector
__all__ = ['HarmDataCollector', 'HarmScraper']

# If run directly, execute the main function from the new module
if __name__ == "__main__":
    import asyncio
    from src.ingestion.harm.harm_data_collector import main
    asyncio.run(main())
