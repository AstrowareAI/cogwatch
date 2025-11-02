"""
Test script to verify MongoDB storage for SpiralBench and Capability collectors
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.ingestion.harm.spiralbench_data_collector import SpiralBenchDataCollector
from src.ingestion.capability_data_collector import CapabilityDataCollector
from src.db.mongodb import get_collection


async def test_collectors():
    """Test both collectors and verify MongoDB storage"""
    
    print("="*70)
    print("MONGODB STORAGE TEST - SpiralBench & Capability Collectors")
    print("="*70)
    
    # Test SpiralBench Collector
    print("\n" + "="*70)
    print("TEST 1: SPIRAL-BENCH DATA COLLECTOR")
    print("="*70)
    
    spiral_collection = get_collection('spiralbench_snapshots')
    initial_spiral_count = spiral_collection.count_documents({})
    print(f"📊 Initial SpiralBench snapshots in MongoDB: {initial_spiral_count}")
    
    print("\n🔄 Running SpiralBench collector...")
    spiral_collector = SpiralBenchDataCollector()
    spiral_result = await spiral_collector.scrape()
    
    final_spiral_count = spiral_collection.count_documents({})
    print(f"\n📊 Final SpiralBench snapshots in MongoDB: {final_spiral_count}")
    
    # Verify SpiralBench storage
    if final_spiral_count > initial_spiral_count:
        print("✅ SpiralBench data successfully stored in MongoDB!")
        latest_spiral = spiral_collection.find_one(sort=[('datetime', -1)])
        if latest_spiral:
            print(f"   Latest snapshot datetime: {latest_spiral.get('datetime')}")
            print(f"   Latest snapshot has metrics: {'metrics' in latest_spiral}")
            print(f"   Latest snapshot success: {latest_spiral.get('success', False)}")
    else:
        print("⚠️  Warning: No new SpiralBench snapshot found in MongoDB")
    
    # Test Capability Collector
    print("\n" + "="*70)
    print("TEST 2: CAPABILITY DATA COLLECTOR")
    print("="*70)
    
    capability_collection = get_collection('capability_snapshots')
    initial_capability_count = capability_collection.count_documents({})
    print(f"📊 Initial Capability snapshots in MongoDB: {initial_capability_count}")
    
    print("\n🔄 Running Capability collector...")
    capability_collector = CapabilityDataCollector()
    capability_result = await capability_collector.scrape()
    
    final_capability_count = capability_collection.count_documents({})
    print(f"\n📊 Final Capability snapshots in MongoDB: {final_capability_count}")
    
    # Verify Capability storage
    if final_capability_count > initial_capability_count:
        print("✅ Capability data successfully stored in MongoDB!")
        latest_capability = capability_collection.find_one(sort=[('datetime', -1)])
        if latest_capability:
            print(f"   Latest snapshot datetime: {latest_capability.get('datetime')}")
            print(f"   Latest snapshot has capabilities: {'capabilities' in latest_capability}")
            print(f"   Latest snapshot success: {latest_capability.get('success', False)}")
            if 'capabilities' in latest_capability:
                capability_types = list(latest_capability['capabilities'].keys())
                print(f"   Capability types: {capability_types}")
    else:
        print("⚠️  Warning: No new Capability snapshot found in MongoDB")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"SpiralBench Collector:")
    print(f"  - Status: {'✅ PASSED' if spiral_result.get('success') else '❌ FAILED'}")
    print(f"  - Snapshots in DB: {final_spiral_count}")
    print(f"  - New snapshots added: {final_spiral_count - initial_spiral_count}")
    
    print(f"\nCapability Collector:")
    print(f"  - Status: {'✅ PASSED' if capability_result.get('success') else '❌ FAILED'}")
    print(f"  - Snapshots in DB: {final_capability_count}")
    print(f"  - New snapshots added: {final_capability_count - initial_capability_count}")
    
    # Overall verification
    print("\n" + "="*70)
    if (final_spiral_count > initial_spiral_count and 
        final_capability_count > initial_capability_count and
        spiral_result.get('success') and 
        capability_result.get('success')):
        print("✅ ALL TESTS PASSED - MongoDB storage working correctly!")
    else:
        print("⚠️  Some tests had issues. Check the output above for details.")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_collectors())

