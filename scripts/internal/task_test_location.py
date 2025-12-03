#!/usr/bin/env python3
"""
Test script to verify location configuration
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import config_settings
from agent.tools import WeatherTool

async def test_location():
    """Test location configuration."""
    print("=" * 60)
    print("LOCATION CONFIGURATION TEST")
    print("=" * 60)
    print()
    
    # Show configured location
    print(f"✓ Configured Location: {config_settings.DEFAULT_LOCATION}")
    print()
    
    # Test weather tool with default location
    print("Testing Weather Tool...")
    print("-" * 60)
    
    weather_tool = WeatherTool()
    
    # Test 1: No location specified (should use default)
    print("\n1. Without location (should use default):")
    result = await weather_tool.execute()
    print(f"   Result: {result}")
    
    # Test 2: Explicit location
    print("\n2. With explicit location (Prague):")
    result = await weather_tool.execute(location="Prague")
    print(f"   Result: {result}")
    
    # Test 3: Another location
    print("\n3. With explicit location (London):")
    result = await weather_tool.execute(location="London")
    print(f"   Result: {result}")
    
    print()
    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    print()
    print(f"Summary:")
    print(f"  • Default location is set to: {config_settings.DEFAULT_LOCATION}")
    print(f"  • All weather queries without explicit location will use this")
    print(f"  • You can override with specific location in the query")
    print()

if __name__ == "__main__":
    asyncio.run(test_location())
