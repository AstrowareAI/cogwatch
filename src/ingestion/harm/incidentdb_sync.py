"""
AI Incident Database MongoDB Sync Script
Imports and syncs incident data to MongoDB for local querying and LLM scoring
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import aiohttp

# For relative imports from sibling directories, we'll import from src package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from db.mongodb import get_collection, create_indexes


class IncidentDBSync:
    """Handles syncing AI Incident Database data to MongoDB"""
    
    def __init__(self, collection_name: str = 'ai_incidents'):
        self.incident_db_url = "https://incidentdatabase.ai/api/graphql"
        self.collection = get_collection(collection_name)
    
    # ============ GraphQL API Methods (embedded scraper functionality) ============
    
    async def execute_query(self, query: str) -> Optional[Dict]:
        """
        Execute a GraphQL query against the AI Incident Database API
        
        Args:
            query: GraphQL query string
            
        Returns:
            Response data dictionary or None if failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.incident_db_url,
                    json={'query': query},
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check for GraphQL errors
                        if 'errors' in data:
                            print(f"GraphQL errors: {data['errors']}")
                            return None
                        return data
                    else:
                        print(f"AI Incident DB API request failed: {response.status}")
                        error_text = await response.text()
                        print(f"Error details: {error_text}")
                        return None
        except Exception as e:
            print(f"Error fetching AI Incident DB data: {e}")
            return None
    
    def build_incident_fields_query(self) -> str:
        """
        Build the fields portion of an incident query (reusable fragment-like structure)
        
        Returns:
            String with GraphQL fields for incident data
        """
        return """
            _id
            title
            date
            date_modified
            incident_id
            description
            created_at
            reports {
                _id
                title
                report_number
                url
                date_published
                date_submitted
                authors
                description
                image_url
                cloudinary_id
                text
            }
            classifications {
                namespace
                attributes {
                    short_name
                    value_json
                }
            }
            AllegedDeployerOfAISystem {
                _id
                entity_id
                name
            }
            AllegedDeveloperOfAISystem {
                _id
                entity_id
                name
            }
            AllegedHarmedOrNearlyHarmedParties {
                _id
                entity_id
                name
            }
            implicated_systems {
                _id
                entity_id
                name
            }
        """
    
    def parse_incident_node(self, node: Dict) -> Dict:
        """
        Parse a single incident node from GraphQL response
        
        Args:
            node: Raw incident node from GraphQL response
            
        Returns:
            Flattened incident dictionary
        """
        incident = {
            '_id': node.get('_id'),
            'incident_id': node.get('incident_id'),
            'title': node.get('title'),
            'date': node.get('date'),
            'date_modified': node.get('date_modified'),
            'created_at': node.get('created_at'),
            'description': node.get('description'),
        }
        
        # Extract reports
        reports_list = node.get('reports', [])
        incident['reports'] = reports_list if isinstance(reports_list, list) else []
        incident['report_count'] = len(incident['reports'])
        
        # Extract classifications
        classifications_list = node.get('classifications', [])
        incident['classifications'] = []
        for cls in classifications_list:
            if isinstance(cls, dict):
                namespace = cls.get('namespace')
                attributes = cls.get('attributes', [])
                for attr in attributes:
                    short_name = attr.get('short_name', '')
                    value_json = attr.get('value_json', '')
                    incident['classifications'].append({
                        'namespace': namespace,
                        'attribute': short_name,
                        'value': value_json
                    })
        
        # Extract entities from various entity fields
        entities = []
        for entity in node.get('AllegedDeployerOfAISystem', []):
            if isinstance(entity, dict):
                entities.append({
                    'name': entity.get('name'),
                    'entity_id': entity.get('entity_id'),
                    'role': 'AllegedDeployerOfAISystem'
                })
        for entity in node.get('AllegedDeveloperOfAISystem', []):
            if isinstance(entity, dict):
                entities.append({
                    'name': entity.get('name'),
                    'entity_id': entity.get('entity_id'),
                    'role': 'AllegedDeveloperOfAISystem'
                })
        for entity in node.get('AllegedHarmedOrNearlyHarmedParties', []):
            if isinstance(entity, dict):
                entities.append({
                    'name': entity.get('name'),
                    'entity_id': entity.get('entity_id'),
                    'role': 'AllegedHarmedOrNearlyHarmedParties'
                })
        for entity in node.get('implicated_systems', []):
            if isinstance(entity, dict):
                entities.append({
                    'name': entity.get('name'),
                    'entity_id': entity.get('entity_id'),
                    'role': 'implicated_systems'
                })
        incident['entities'] = entities
        
        return incident
    
    def parse_incidents_response(self, data: Dict) -> List[Dict]:
        """
        Parse incidents from GraphQL response
        
        Args:
            data: GraphQL response data
            
        Returns:
            List of parsed incident dictionaries
        """
        incidents = []
        
        if 'data' in data and 'incidents' in data['data']:
            incidents_list = data['data']['incidents']
            
            for node in incidents_list:
                incident = self.parse_incident_node(node)
                incidents.append(incident)
        
        return incidents
    
    def build_query_by_date_range(self, start_date: str, end_date: Optional[str] = None, limit: int = 100) -> str:
        """
        Build query for incidents in a date range
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format), if None uses current date
            limit: Maximum number of incidents to fetch
            
        Returns:
            Complete GraphQL query string
        """
        fields = self.build_incident_fields_query()
        
        # Format date filter
        start_date_str = start_date.replace('+00:00', 'Z').replace(' ', 'T')
        if end_date:
            end_date_str = end_date.replace('+00:00', 'Z').replace(' ', 'T')
            filter_conditions = f'date_modified: {{ GTE: "{start_date_str}", LTE: "{end_date_str}" }}'
        else:
            filter_conditions = f'date_modified: {{ GTE: "{start_date_str}" }}'
        
        return f"""
        query {{
            incidents(
                filter: {{
                    {filter_conditions}
                }}
                sort: {{date_modified: DESC}}
                pagination: {{limit: {limit}}}
            ) {{
                {fields}
            }}
        }}
        """
    
    async def fetch_by_date_range(self, days: int = 7, limit: int = 100) -> Dict:
        """
        Fetch incidents from the last N days (helper method for API access)
        
        Args:
            days: Number of days to look back (default: 7)
            limit: Maximum number of incidents to fetch
            
        Returns:
            Dictionary with success status, incidents, and summary
        """
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        print(f"Fetching incidents from the last {days} days (since {cutoff_date})...")
        
        query = self.build_query_by_date_range(start_date=cutoff_date, limit=limit)
        data = await self.execute_query(query)
        
        if not data:
            return {
                'success': False,
                'error': 'Failed to fetch recent AI Incident DB data',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        incidents = self.parse_incidents_response(data)
        
        # Calculate summary statistics
        total_reports = sum(inc.get('report_count', 0) for inc in incidents)
        incidents_with_classifications = [inc for inc in incidents if inc.get('classifications')]
        
        return {
            'success': True,
            'source': self.incident_db_url,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'days_lookback': days,
            'cutoff_date': cutoff_date,
            'incidents': incidents,
            'summary': {
                'total_incidents': len(incidents),
                'total_reports': total_reports,
                'incidents_with_classifications': len(incidents_with_classifications)
            }
        }
    
    async def fetch_recent_from_api(self, limit: int = 100) -> Dict:
        """
        Fetch recent incidents from API (helper method for harm_scraper)
        
        Args:
            limit: Maximum number of incidents to fetch
            
        Returns:
            Dictionary with success status, incidents, and summary
        """
        print(f"Fetching recent AI Incident DB data from {self.incident_db_url}...")
        
        fields = self.build_incident_fields_query()
        query = f"""
        query {{
            incidents(
                sort: {{date_modified: DESC}}
                pagination: {{limit: {limit}}}
            ) {{
                {fields}
            }}
        }}
        """
        
        data = await self.execute_query(query)
        
        if not data:
            return {
                'success': False,
                'error': 'Failed to fetch AI Incident DB data',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        incidents = self.parse_incidents_response(data)
        print(f"Fetched {len(incidents)} incidents")
        
        # Calculate summary statistics
        total_reports = sum(inc.get('report_count', 0) for inc in incidents)
        incidents_with_classifications = [inc for inc in incidents if inc.get('classifications')]
        
        return {
            'success': True,
            'source': self.incident_db_url,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'incidents': incidents,
            'summary': {
                'total_incidents': len(incidents),
                'total_reports': total_reports,
                'incidents_with_classifications': len(incidents_with_classifications),
            }
        }
    
    # ============ MongoDB Sync Methods ============
        
    async def fetch_all_incidents(self, batch_size: int = 500) -> List[Dict]:
        """
        Fetch all incidents from the API in batches
        
        Args:
            batch_size: Number of incidents to fetch per batch
            
        Returns:
            List of all incident dictionaries
        """
        all_incidents = []
        offset = 0
        
        print(f"Fetching all incidents (batch size: {batch_size})...")
        
        while True:
            # Build query with pagination
            fields = self.build_incident_fields_query()
            query = f"""
            query {{
                incidents(
                    sort: {{incident_id: ASC}}
                    pagination: {{limit: {batch_size}, skip: {offset}}}
                ) {{
                    {fields}
                }}
            }}
            """
            
            data = await self.execute_query(query)
            
            if not data:
                print(f"No data returned at offset {offset}, stopping")
                break
            
            incidents = self.parse_incidents_response(data)
            
            if not incidents:
                print(f"No incidents returned at offset {offset}, stopping")
                break
            
            all_incidents.extend(incidents)
            print(f"Fetched {len(incidents)} incidents (total so far: {len(all_incidents)})")
            
            # If we got fewer than batch_size, we're done
            if len(incidents) < batch_size:
                break
            
            offset += batch_size
        
        print(f"Total incidents fetched: {len(all_incidents)}")
        return all_incidents
    
    def prepare_incident_for_db(self, incident: Dict) -> Dict:
        """
        Prepare incident document for MongoDB storage
        
        Args:
            incident: Raw incident dictionary from scraper
            
        Returns:
            Document ready for MongoDB insertion
        """
        doc = {
            **incident,
            'synced_at': datetime.now(timezone.utc),
            'urgency_score': None,  # Will be populated by LLM later
            'urgency_score_updated_at': None,
        }
        
        # Ensure date_modified is a datetime if it's a string
        if isinstance(doc.get('date_modified'), str):
            try:
                doc['date_modified'] = datetime.fromisoformat(
                    doc['date_modified'].replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass
        
        # Ensure created_at is a datetime if it's a string
        if isinstance(doc.get('created_at'), str):
            try:
                doc['created_at'] = datetime.fromisoformat(
                    doc['created_at'].replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass
        
        return doc
    
    def upsert_incident(self, incident: Dict) -> bool:
        """
        Upsert a single incident into MongoDB
        
        Args:
            incident: Incident dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            prepared = self.prepare_incident_for_db(incident)
            incident_id = prepared.get('incident_id')
            
            if incident_id is None:
                print("Warning: Incident missing incident_id, skipping")
                return False
            
            # Upsert using incident_id as unique key
            result = self.collection.update_one(
                {'incident_id': incident_id},
                {'$set': prepared},
                upsert=True
            )
            
            return result.acknowledged
        except Exception as e:
            print(f"Error upserting incident {incident.get('incident_id')}: {e}")
            return False
    
    async def initial_import(self, batch_size: int = 10) -> Dict:
        """
        Perform initial full import of all incidents
        
        Args:
            batch_size: Number of incidents to fetch per API request (default: 10)
        
        Returns:
            Dictionary with import statistics
        """
        print("=" * 60)
        print("INITIAL IMPORT: Fetching all incidents from AI Incident DB")
        print("=" * 60)
        
        # Create indexes first
        create_indexes(self.collection)
        
        # Fetch all incidents (smaller batch size to avoid API response size limits)
        incidents = await self.fetch_all_incidents(batch_size=batch_size)
        
        if not incidents:
            return {
                'success': False,
                'error': 'No incidents fetched',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Upsert all incidents
        print(f"\nUpserting {len(incidents)} incidents into MongoDB...")
        success_count = 0
        error_count = 0
        
        for i, incident in enumerate(incidents, 1):
            if self.upsert_incident(incident):
                success_count += 1
            else:
                error_count += 1
            
            if i % 50 == 0:
                print(f"  Processed {i}/{len(incidents)} incidents...")
        
        print(f"\nImport complete: {success_count} successful, {error_count} errors")
        
        # Get final count from DB
        total_in_db = self.collection.count_documents({})
        
        return {
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_fetched': len(incidents),
            'successful_upserts': success_count,
            'errors': error_count,
            'total_in_database': total_in_db
        }
    
    def get_max_incident_id(self) -> Optional[int]:
        """
        Get the maximum incident_id currently in the database
        
        Returns:
            Maximum incident_id or None if database is empty
        """
        result = self.collection.find_one(
            sort=[('incident_id', -1)],
            projection={'incident_id': 1}
        )
        return result.get('incident_id') if result else None
    
    async def incremental_sync(self, days_back: int = 30, use_incident_id: bool = True) -> Dict:
        """
        Perform incremental sync - fetches new or updated incidents
        
        Args:
            days_back: Number of days to look back for modified incidents (if use_incident_id=False)
            use_incident_id: If True, fetch incidents with incident_id > max in DB.
                           If False, fetch incidents modified in last N days.
            
        Returns:
            Dictionary with sync statistics
        """
        print("=" * 60)
        
        # Ensure indexes exist
        create_indexes(self.collection)
        
        if use_incident_id:
            # Smart sync: only fetch incidents with ID greater than what we have
            max_id = self.get_max_incident_id()
            
            if max_id is None:
                print("No incidents in DB yet. Running initial import instead...")
                return await self.initial_import(batch_size=10)
            
            print(f"INCREMENTAL SYNC: Fetching incidents with incident_id > {max_id}")
            print("=" * 60)
            
            # Fetch all incidents with ID greater than max
            incidents = []
            current_max = max_id
            batch_size = 10
            
            while True:
                # Build query for incidents with ID > current_max
                fields = self.build_incident_fields_query()
                query = f"""
                query {{
                    incidents(
                        filter: {{
                            incident_id: {{
                                GT: {current_max}
                            }}
                        }}
                        sort: {{incident_id: ASC}}
                        pagination: {{limit: {batch_size}}}
                    ) {{
                        {fields}
                    }}
                }}
                """
                
                data = await self.execute_query(query)
                
                if not data:
                    break
                
                batch_incidents = self.parse_incidents_response(data)
                
                if not batch_incidents:
                    break
                
                incidents.extend(batch_incidents)
                print(f"Fetched {len(batch_incidents)} incidents (total so far: {len(incidents)})")
                
                # Update current_max to the highest ID in this batch
                batch_max = max(inc.get('incident_id', 0) for inc in batch_incidents if inc.get('incident_id'))
                if batch_max <= current_max:
                    break
                
                current_max = batch_max
                
                # If we got fewer than batch_size, we're done
                if len(batch_incidents) < batch_size:
                    break
            
            if not incidents:
                print("No new incidents found")
                return {
                    'success': True,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'incidents_synced': 0,
                    'message': f'No incidents with incident_id > {max_id}',
                    'max_incident_id_in_db': max_id
                }
            
            result_data = {'incidents': incidents}
        else:
            # Legacy method: use date_modified
            print(f"INCREMENTAL SYNC: Fetching incidents from last {days_back} days")
            print("=" * 60)
            
            result = await self.fetch_by_date_range(days=days_back, limit=500)
            
            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            result_data = result
        
        incidents = result_data.get('incidents', [])
        
        if not incidents:
            if use_incident_id:
                print("No new incidents found")
            else:
                print("No incidents found in date range")
            return {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'incidents_synced': 0,
                'message': 'No new or updated incidents found'
            }
        
        print(f"Found {len(incidents)} incidents to sync")
        
        # Upsert all incidents
        success_count = 0
        error_count = 0
        new_count = 0
        updated_count = 0
        
        for incident in incidents:
            incident_id = incident.get('incident_id')
            existing = self.collection.find_one({'incident_id': incident_id})
            is_new = existing is None
            
            if self.upsert_incident(incident):
                success_count += 1
                if is_new:
                    new_count += 1
                else:
                    updated_count += 1
            else:
                error_count += 1
        
        print("\nSync complete:")
        print(f"  New incidents: {new_count}")
        print(f"  Updated incidents: {updated_count}")
        print(f"  Errors: {error_count}")
        
        # Get total count from DB
        total_in_db = self.collection.count_documents({})
        
        result_dict = {
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'incidents_synced': success_count,
            'new_incidents': new_count,
            'updated_incidents': updated_count,
            'errors': error_count,
            'total_in_database': total_in_db,
        }
        
        if use_incident_id:
            max_id = self.get_max_incident_id()
            result_dict['max_incident_id_in_db'] = max_id
        else:
            result_dict['days_lookback'] = days_back
        
        return result_dict


async def main():
    """CLI entry point for sync script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync AI Incident Database to MongoDB')
    parser.add_argument(
        '--mode',
        choices=['initial', 'incremental'],
        default='incremental',
        help='Sync mode: initial (full import) or incremental (recent changes)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='For incremental mode: number of days to look back (default: 30)'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='ai_incidents',
        help='MongoDB collection name (default: ai_incidents)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for API requests (default: 10, increase if needed or reduce if you get response size errors)'
    )
    parser.add_argument(
        '--use-date-sync',
        action='store_true',
        help='Use date_modified for incremental sync instead of incident_id (default: uses incident_id)'
    )
    
    args = parser.parse_args()
    
    sync = IncidentDBSync(collection_name=args.collection)
    
    if args.mode == 'initial':
        result = await sync.initial_import(batch_size=args.batch_size)
    else:
        result = await sync.incremental_sync(
            days_back=args.days,
            use_incident_id=not args.use_date_sync
        )
    
    print("\n" + "=" * 60)
    print("SYNC RESULT")
    print("=" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
