"""
Harm/Misalignment Data Scraper for Cogwatch
DEPRECATED: This file is kept for backward compatibility.
Please use src.ingestion.harm.harm_scraper.HarmScraper instead.
"""

# Import from the new modular location
# Handle both relative imports (when used as module) and absolute imports (when run directly)
try:
    from .harm.harm_scraper import HarmScraper
except ImportError:
    # Fallback for direct script execution
    import sys
    import os
    # Add parent directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.ingestion.harm.harm_scraper import HarmScraper

# Export for backward compatibility
__all__ = ['HarmScraper']

# If run directly, execute the main function from the new module
if __name__ == "__main__":
    import asyncio
    from src.ingestion.harm.harm_scraper import main
    asyncio.run(main())
