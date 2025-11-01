# AI Incident Database MongoDB Sync

This document describes how to sync AI Incident Database data to MongoDB for local querying and LLM-based urgency scoring.

## Setup

1. **Environment Configuration**:
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` with your MongoDB connection details:
   ```env
   MONGODB_URI=mongodb://localhost:27017/
   COGWATCH_DB_NAME=cogwatch
   ```
   
   For MongoDB Atlas:
   ```env
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   COGWATCH_DB_NAME=cogwatch
   ```

2. **Initial Full Import**:
   ```bash
   cd /path/to/cogwatch
   python -m src.ingestion.harm.incidentdb_sync --mode initial
   
   # Adjust batch size if needed (default: 10)
   python -m src.ingestion.harm.incidentdb_sync --mode initial --batch-size 25
   ```
   
   This will:
   - Fetch all incidents from the AI Incident Database API in batches (default: 10 per batch)
   - Store them in MongoDB collection `ai_incidents`
   - Create necessary indexes for efficient querying

3. **Periodic Incremental Sync**:
   ```bash
   cd /path/to/cogwatch
   
   # Default: Syncs only new incidents (incident_id > max in DB) - RECOMMENDED
   python -m src.ingestion.harm.incidentdb_sync --mode incremental
   
   # Use date-based sync (if you need to catch updates to old incidents)
   python -m src.ingestion.harm.incidentdb_sync --mode incremental --use-date-sync --days 30
   
   # Sync incidents from last 7 days (date-based)
   python -m src.ingestion.harm.incidentdb_sync --mode incremental --use-date-sync --days 7
   
   # Custom collection name
   python -m src.ingestion.harm.incidentdb_sync --mode incremental --collection my_incidents
   
   # Adjust batch size if needed (default: 10)
   python -m src.ingestion.harm.incidentdb_sync --mode incremental --batch-size 25
   ```

## Database Schema

Each incident document in MongoDB has the following structure:

```python
{
    '_id': ObjectId,                    # MongoDB auto-generated
    'incident_id': int,                 # Unique ID from source (indexed, unique)
    'title': str,
    'date': str,                        # ISO date string
    'date_modified': datetime,          # Last modification time (indexed)
    'created_at': datetime,             # Creation time (indexed)
    'description': str,
    'reports': [                        # List of report dictionaries
        {
            'title': str,
            'report_number': int,
            'url': str,
            'date_published': str,
            ...
        }
    ],
    'classifications': [                # List of classification dictionaries
        {
            'namespace': str,
            'attribute': str,
            'value': str
        }
    ],
    'entities': [                       # List of entity dictionaries
        {
            'name': str,
            'entity_id': str,
            'role': str                  # e.g., 'AllegedDeployerOfAISystem'
        }
    ],
    'report_count': int,
    'synced_at': datetime,              # When this document was last synced
    'urgency_score': None,              # LLM-generated urgency score (populated later)
    'urgency_score_updated_at': None    # When urgency score was last updated
}
```

## Indexes

The following indexes are automatically created for efficient querying:

- `incident_id` (unique) - Fast lookups by incident ID
- `date_modified` - Efficient date range queries
- `created_at` - Track when incidents were created
- `synced_at` - Track sync operations
- `urgency_score` - Future LLM scoring queries

## Usage with Cron/Scheduler

For automatic syncing (daily or twice a week), you can use cron or a task scheduler:

```bash
# RECOMMENDED: Sync twice a week (Monday and Thursday at 2 AM) - uses incident_id-based sync
0 2 * * 1,4 cd /path/to/cogwatch && python -m src.ingestion.harm.incidentdb_sync --mode incremental

# Or sync daily - only fetches new incidents (incident_id > max in DB)
0 2 * * * cd /path/to/cogwatch && python -m src.ingestion.harm.incidentdb_sync --mode incremental

# Alternative: Use date-based sync if you need to catch updates to old incidents
0 2 * * 1,4 cd /path/to/cogwatch && python -m src.ingestion.harm.incidentdb_sync --mode incremental --use-date-sync --days 14

# Sync weekly with date-based method (looks back 7 days)
0 2 * * 0 cd /path/to/cogwatch && python -m src.ingestion.harm.incidentdb_sync --mode incremental --use-date-sync --days 7
```

**Sync Methods**:
- **Default (recommended)**: Uses `incident_id`-based syncing - only fetches incidents where `incident_id > max(incident_id in DB)`. Fast and efficient.
- **Date-based (`--use-date-sync`)**: Fetches incidents modified in the last N days. Use this if you need to catch updates to existing incidents or if incident IDs might not always be sequential.

## Next Steps: LLM Urgency Scoring

After syncing incidents, you can run batch LLM scoring on the `urgency_score` field:

```python
from src.db.mongodb import get_collection

collection = get_collection('ai_incidents')

# Find incidents without urgency scores
uns scored = collection.find({'urgency_score': None})

# Process with LLM and update
for incident in unscored:
    score = await llm_score_incident(incident)
    collection.update_one(
        {'_id': incident['_id']},
        {'$set': {
            'urgency_score': score,
            'urgency_score_updated_at': datetime.now(timezone.utc)
        }}
    )
```
