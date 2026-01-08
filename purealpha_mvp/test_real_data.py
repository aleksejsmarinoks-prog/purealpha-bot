"""
Test script для проверки real data ingestion
Запусти: python test_real_data.py
"""
import sys
import logging
from src.data_ingestion_real import RealDataIngestion

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

def main():
    print("=" * 70)
    print("PUREALPHA 3.1 - REAL DATA INGESTION TEST")
    print("=" * 70)
    print()
    
    # Initialize
    print("Initializing data sources...")
    ingestion = RealDataIngestion()
    print()
    
    # Get available parameters
    print("Available parameters:")
    params = ingestion.get_available_parameters()
    for i, param in enumerate(params, 1):
        print(f"  {i}. {param}")
    print(f"\nTotal: {len(params)} parameters")
    print()
    
    # Fetch all data
    input("Press Enter to fetch real data...")
    print()
    
    data = ingestion.fetch_all_parameters()
    print()
    
    # Validate
    is_valid, warnings = ingestion.validate_data(data)
    print()
    print("=" * 70)
    print(f"VALIDATION: {'PASSED ✓' if is_valid else 'FAILED ✗'}")
    print("=" * 70)
    
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  ⚠️  {w}")
    
    # Display sample data
    print("\nSample data (first 10 parameters):")
    for i, (param, value) in enumerate(list(data.items())[:10], 1):
        if value is not None:
            print(f"  {i}. {param}: {value:.4f}")
        else:
            print(f"  {i}. {param}: NULL")
    
    # Stats
    stats = ingestion.get_fetch_stats()
    print(f"\nFetch stats:")
    print(f"  Total fetches: {stats['total_fetches']}")
    print(f"  Parameters fetched: {stats['last_parameters_count']}")
    print(f"  Sources available:")
    for source, available in stats['sources_available'].items():
        status = "✓" if available else "✗"
        print(f"    {status} {source}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
