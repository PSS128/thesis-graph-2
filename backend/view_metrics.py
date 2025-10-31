#!/usr/bin/env python3
"""
View metrics from the thesis-graph backend.
Run this script to see LLM performance, cache stats, and prompt versions.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def view_llm_metrics(hours=24):
    """View LLM performance metrics."""
    print_section(f"LLM PERFORMANCE METRICS (Last {hours} hours)")

    try:
        response = requests.get(f"{BASE_URL}/metrics/llm?hours={hours}")
        response.raise_for_status()
        data = response.json()

        print(f"\nOverall Statistics:")
        print(f"  Total Calls:       {data['total_calls']}")
        print(f"  Successful:        {data['successful_calls']} ({data['successful_calls']/data['total_calls']*100:.1f}% success rate)" if data['total_calls'] > 0 else "  No calls yet")
        print(f"  Failed:            {data['failed_calls']}")
        print(f"  Cache Hits:        {data['cache_hits']}")
        print(f"  Cache Misses:      {data['cache_misses']}")
        print(f"  Avg Latency:       {data['avg_latency_ms']:.2f} ms")

        if data.get('total_input_tokens'):
            print(f"  Total Input Tokens:  {data['total_input_tokens']}")
            print(f"  Total Output Tokens: {data['total_output_tokens']}")

        print(f"\nBreakdown by Prompt Type:")
        for prompt_type, stats in data['by_prompt_type'].items():
            print(f"\n  {prompt_type}:")
            print(f"    Calls:           {stats['total_calls']}")
            print(f"    Success Rate:    {stats['success_rate_percent']:.1f}%")
            print(f"    Cache Hit Rate:  {stats['cache_hit_rate_percent']:.1f}%")
            print(f"    Avg Latency:     {stats['avg_latency_ms']:.2f} ms")

        print(f"\nBreakdown by Version:")
        for version, stats in data['by_version'].items():
            print(f"\n  Version {version}:")
            print(f"    Calls:           {stats['total_calls']}")
            print(f"    Successful:      {stats['successful_calls']}")
            print(f"    Avg Latency:     {stats['avg_latency_ms']:.2f} ms")

    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend. Is it running?")
        print("Start with: cd backend && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"ERROR: {e}")


def view_cache_stats():
    """View cache performance statistics."""
    print_section("CACHE PERFORMANCE STATISTICS")

    try:
        response = requests.get(f"{BASE_URL}/metrics/cache")
        response.raise_for_status()
        data = response.json()

        print(f"\nOverall Cache Performance:")
        print(f"  Total Cache Entries:  {data['total_cache_entries']}")
        print(f"  Total Requests:       {data['total_requests']}")
        print(f"  Cache Hits:           {data['total_hits']}")
        print(f"  Cache Misses:         {data['total_misses']}")
        print(f"  Overall Hit Rate:     {data['overall_hit_rate_percent']:.2f}%")

        if data['total_requests'] > 0:
            savings_estimate = data['total_hits'] * 2  # Rough estimate: 2 seconds saved per hit
            print(f"  Est. Time Saved:      ~{savings_estimate} seconds")

        print(f"\nBreakdown by Operation Type:")
        for op_type, stats in data['breakdown_by_type'].items():
            print(f"\n  {op_type}:")
            print(f"    Total Requests:  {stats['total_requests']}")
            print(f"    Hits:            {stats['hits']}")
            print(f"    Misses:          {stats['misses']}")
            print(f"    Hit Rate:        {stats['hit_rate_percent']:.2f}%")

    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend. Is it running?")
    except Exception as e:
        print(f"ERROR: {e}")


def view_prompt_versions():
    """View active prompt versions and changelogs."""
    print_section("PROMPT VERSIONS & CHANGELOGS")

    try:
        response = requests.get(f"{BASE_URL}/metrics/prompts")
        response.raise_for_status()
        data = response.json()

        print(f"\nActive Versions:")
        for prompt_type, version in data['active_versions'].items():
            print(f"  {prompt_type:20s} -> v{version}")

        print(f"\nChangelogs:")
        for prompt_type, changelog in data['changelogs'].items():
            print(f"\n  {prompt_type}:")
            for entry in sorted(changelog, key=lambda x: x['version'], reverse=True):
                status = "[ACTIVE]" if entry['is_active'] else "[OLD]   "
                print(f"    {status} v{entry['version']} ({entry['date_introduced']})")
                print(f"             {entry['changes']}")

    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend. Is it running?")
    except Exception as e:
        print(f"ERROR: {e}")


def clear_cache(prefix=None):
    """Clear the cache."""
    print_section("CLEAR CACHE")

    try:
        url = f"{BASE_URL}/metrics/cache/clear"
        if prefix:
            url += f"?prefix={prefix}"
            print(f"\nClearing cache for prefix: {prefix}...")
        else:
            print(f"\nClearing ALL cache entries...")

        response = requests.post(url)
        response.raise_for_status()
        data = response.json()

        print(f"[SUCCESS] {data['message']}")

    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend. Is it running?")
    except Exception as e:
        print(f"ERROR: {e}")


def main():
    """Main function to display all metrics."""
    print("\n")
    print("+" + "=" * 78 + "+")
    print("|" + " " * 20 + "THESIS-GRAPH METRICS DASHBOARD" + " " * 28 + "|")
    print("+" + "=" * 78 + "+")

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "llm":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            view_llm_metrics(hours)
        elif command == "cache":
            view_cache_stats()
        elif command == "prompts":
            view_prompt_versions()
        elif command == "clear":
            prefix = sys.argv[2] if len(sys.argv) > 2 else None
            clear_cache(prefix)
        else:
            print(f"\nUnknown command: {command}")
            print("\nUsage:")
            print("  python view_metrics.py llm [hours]      - View LLM metrics (default: 24 hours)")
            print("  python view_metrics.py cache            - View cache statistics")
            print("  python view_metrics.py prompts          - View prompt versions")
            print("  python view_metrics.py clear [prefix]   - Clear cache (optionally by prefix)")
            print("  python view_metrics.py                  - View all metrics")
    else:
        # Show all metrics
        view_llm_metrics()
        view_cache_stats()
        view_prompt_versions()

    print("\n" + "=" * 80)
    print()


if __name__ == "__main__":
    main()
