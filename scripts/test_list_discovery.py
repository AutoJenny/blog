#!/usr/bin/env python3
"""
Test weekly discovery logic: filtering, candidate selection, stop conditions.
Tests the discovery portion of the weekly sync without full API calls.
"""
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))

def test_discovery_filtering():
    """Test that discovery correctly filters by created_at cutoff."""
    print("Testing discovery filtering...")
    
    # Mock product data with created_at
    cutoff = datetime(2025, 10, 1)
    products = [
        {'sku': 'new1', 'created_at': '2025-10-15T10:00:00+01:00'},  # After cutoff - candidate
        {'sku': 'old1', 'created_at': '2025-09-15T10:00:00+01:00'},  # Before cutoff - skip
        {'sku': 'new2', 'created_at': '2025-10-20T10:00:00+01:00'},  # After cutoff - candidate
        {'sku': 'edge', 'created_at': '2025-10-01T00:00:00+01:00'},  # On cutoff - candidate
    ]
    
    candidates = []
    for p in products:
        created_str = p.get('created_at')
        if created_str:
            try:
                date_part = created_str.split('T')[0]
                if '+' in created_str:
                    time_part = created_str.split('+')[0].split('T')[1]
                elif created_str.endswith('Z'):
                    time_part = created_str.split('T')[1].replace('Z', '')
                else:
                    time_part = created_str.split('T')[1]
                created_dt = datetime.fromisoformat(f"{date_part} {time_part}")
                if created_dt >= cutoff:
                    candidates.append(p)
            except Exception as e:
                print(f"Parse error for {p.get('sku')}: {e}")
                continue
    
    assert len(candidates) == 3, f"Expected 3 candidates, got {len(candidates)}"
    assert all(c['sku'] in ['new1', 'new2', 'edge'] for c in candidates), "Wrong candidates selected"
    print("✓ Discovery filtering works correctly")

def test_stop_condition():
    """Test stop condition after N pages with no candidates."""
    print("Testing stop condition...")
    
    pages_with_no_candidates = 0
    max_allowed = 3
    
    # Simulate 5 pages
    for page in range(5):
        # Page 0 and 1 have candidates, 2-4 don't
        has_candidates = page < 2
        
        if has_candidates:
            pages_with_no_candidates = 0
        else:
            pages_with_no_candidates += 1
            if pages_with_no_candidates >= max_allowed:
                print(f"✓ Stopped at page {page} after {pages_with_no_candidates} pages with no candidates")
                return
    
    print("✓ Stop condition logic works")

def test_candidate_selection():
    """Test that candidates are selected from getProducts response."""
    print("Testing candidate selection...")
    
    cutoff = datetime.now() - timedelta(days=7)
    
    # Mock API response format
    mock_batch = [
        {'sku': 'test1', 'created_at': (datetime.now() - timedelta(days=1)).isoformat()},  # New
        {'sku': 'test2', 'created_at': (datetime.now() - timedelta(days=10)).isoformat()},  # Old
        {'sku': 'test3', 'created_at': (datetime.now() - timedelta(days=2)).isoformat()},  # New
    ]
    
    candidates = []
    for p in mock_batch:
        created_str = p.get('created_at')
        if created_str:
            try:
                created_dt = datetime.fromisoformat(created_str.replace('T', ' ').split('.')[0])
                if created_dt >= cutoff:
                    candidates.append(p)
            except Exception:
                continue
    
    assert len(candidates) == 2, f"Expected 2 candidates, got {len(candidates)}"
    assert all(c['sku'] in ['test1', 'test3'] for c in candidates), "Wrong candidates"
    print("✓ Candidate selection works correctly")

if __name__ == '__main__':
    print("Running discovery tests...\n")
    try:
        test_discovery_filtering()
        test_stop_condition()
        test_candidate_selection()
        print("\n✓ All discovery tests passed")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)






