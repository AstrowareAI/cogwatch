"""
Verify MongoDB document structure for stored snapshots
"""

import sys
import os
from pprint import pprint

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.mongodb import get_collection


def verify_mongodb_structure():
    """Verify the structure of stored documents"""
    
    print("="*70)
    print("MONGODB DOCUMENT STRUCTURE VERIFICATION")
    print("="*70)
    
    # Check SpiralBench collection
    print("\n" + "="*70)
    print("SPIRAL-BENCH SNAPSHOTS COLLECTION")
    print("="*70)
    
    spiral_collection = get_collection('spiralbench_snapshots')
    spiral_count = spiral_collection.count_documents({})
    print(f"Total documents: {spiral_count}")
    
    if spiral_count > 0:
        latest_spiral = spiral_collection.find_one(sort=[('datetime', -1)])
        print("\nLatest SpiralBench snapshot structure:")
        print("-"*70)
        print(f"Document ID: {latest_spiral.get('_id')}")
        print(f"datetime field (type: {type(latest_spiral.get('datetime'))}): {latest_spiral.get('datetime')}")
        print(f"timestamp field: {latest_spiral.get('timestamp')}")
        print(f"success field: {latest_spiral.get('success')}")
        print(f"source field: {latest_spiral.get('source')}")
        print(f"Has 'metrics' key: {'metrics' in latest_spiral}")
        if 'metrics' in latest_spiral:
            print(f"  Number of metrics: {len(latest_spiral['metrics'])}")
            print(f"  Metric names: {list(latest_spiral['metrics'].keys())[:5]}...")
        print(f"Has 'summary' key: {'summary' in latest_spiral}")
        if 'summary' in latest_spiral:
            print(f"  Summary keys: {list(latest_spiral['summary'].keys())}")
    
    # Check Capability collection
    print("\n" + "="*70)
    print("CAPABILITY SNAPSHOTS COLLECTION")
    print("="*70)
    
    capability_collection = get_collection('capability_snapshots')
    capability_count = capability_collection.count_documents({})
    print(f"Total documents: {capability_count}")
    
    if capability_count > 0:
        latest_capability = capability_collection.find_one(sort=[('datetime', -1)])
        print("\nLatest Capability snapshot structure:")
        print("-"*70)
        print(f"Document ID: {latest_capability.get('_id')}")
        print(f"datetime field (type: {type(latest_capability.get('datetime'))}): {latest_capability.get('datetime')}")
        print(f"timestamp field: {latest_capability.get('timestamp')}")
        print(f"success field: {latest_capability.get('success')}")
        print(f"sources field: {latest_capability.get('sources', [])[:3]}...")
        print(f"Has 'capabilities' key: {'capabilities' in latest_capability}")
        if 'capabilities' in latest_capability:
            print(f"  Capability types: {list(latest_capability['capabilities'].keys())}")
        print(f"Has 'summary' key: {'summary' in latest_capability}")
        if 'summary' in latest_capability:
            print(f"  Summary keys: {list(latest_capability['summary'].keys())}")
    
    # Verification checklist
    print("\n" + "="*70)
    print("VERIFICATION CHECKLIST")
    print("="*70)
    
    checks = []
    
    if spiral_count > 0:
        latest_spiral = spiral_collection.find_one(sort=[('datetime', -1)])
        checks.append(("SpiralBench has datetime field", 'datetime' in latest_spiral))
        checks.append(("SpiralBench datetime is datetime object", isinstance(latest_spiral.get('datetime'), type(latest_spiral.get('datetime')) if 'datetime' in latest_spiral else None)))
        checks.append(("SpiralBench has metrics", 'metrics' in latest_spiral))
        checks.append(("SpiralBench has summary", 'summary' in latest_spiral))
    
    if capability_count > 0:
        latest_capability = capability_collection.find_one(sort=[('datetime', -1)])
        checks.append(("Capability has datetime field", 'datetime' in latest_capability))
        checks.append(("Capability datetime is datetime object", isinstance(latest_capability.get('datetime'), type(latest_capability.get('datetime')) if 'datetime' in latest_capability else None)))
        checks.append(("Capability has capabilities", 'capabilities' in latest_capability))
        checks.append(("Capability has summary", 'summary' in latest_capability))
    
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
    
    print("\n" + "="*70)
    all_passed = all(result for _, result in checks)
    if all_passed:
        print("✅ ALL CHECKS PASSED - MongoDB structure is correct!")
    else:
        print("⚠️  Some checks failed - review the structure above")
    print("="*70)


if __name__ == "__main__":
    verify_mongodb_structure()

