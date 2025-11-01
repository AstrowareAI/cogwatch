# ArXiv Data Collector - Notes

## Limits & New Papers

### ArXiv API Limits
- **Maximum per request**: 2,000 results
- **Maximum per query**: 30,000 results
- **50 is NOT a limit** - it was just a test value

### How New Papers Are Caught

The collector is configured to **fetch ALL matching papers** by default (`fetch_all=True`). This means:

1. **First run**: Fetches all papers matching your query (up to 30,000)
2. **Subsequent runs**: 
   - Fetches ALL papers again (including new ones)
   - Deduplicates using `arxiv_id`
   - Only inserts papers that don't exist yet

### Sorting Strategy

Papers are sorted by `SubmittedDate` in **descending order** (newest first), so:
- New papers will appear at the top of results
- They'll be processed and stored first
- Deduplication ensures we don't store them twice

### Configuration

```python
from src.ingestion.arxiv import ArxivDataCollector

# Default: fetch_all=True (fetches ALL matching papers, up to 30,000)
collector = ArxivDataCollector()  # Gets all papers

# Limit results for testing
collector = ArxivDataCollector(max_results=50, fetch_all=False)  # Only 50 papers
```

### Example: What Happens with New Papers

**Initial state**: Database has 50 papers

**New papers published**: 20 new papers are published on ArXiv

**Next run**:
1. Searches ArXiv → finds 70 total papers (50 existing + 20 new)
2. Checks existing papers in database → finds 50 matches
3. Inserts 20 new papers
4. Skips 50 existing papers

**Result**: Database now has 70 papers ✅

### Performance Note

- `fetch_all=True` may take longer for large result sets (can be a few minutes)
- The arxiv library handles pagination internally
- If you have >30,000 matching papers, you'd need to refine the query

