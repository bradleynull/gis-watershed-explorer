#!/usr/bin/env python3
"""CLI client for GIS Home Planner API - consumes same API as web UI."""
import argparse
import sys

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx", file=sys.stderr)
    sys.exit(1)

BASE = "http://127.0.0.1:8000"


def main():
    p = argparse.ArgumentParser(description="GIS Home Planner CLI")
    p.add_argument("--health", action="store_true", help="Check API health")
    p.add_argument("--flow", metavar="LAT,LON", help="Flow direction at lat,lon")
    p.add_argument("--flood", metavar="LAT,LON", help="Flood zone at lat,lon")
    p.add_argument("--buildability", metavar="LAT,LON", help="Buildability at lat,lon")
    args = p.parse_args()

    if args.health:
        r = httpx.get(f"{BASE}/health", timeout=5)
        print(r.json())
        sys.exit(0 if r.status_code == 200 else 1)

    if args.flow:
        lat, lon = args.flow.split(",")
        r = httpx.get(f"{BASE}/api/hydrology/flow-direction", params={"lat": lat, "lon": lon}, timeout=15)
        if r.status_code != 200:
            print(r.text, file=sys.stderr)
            sys.exit(1)
        data = r.json()
        print("Flow path:", len(data.get("geometry", {}).get("coordinates", [])), "points")
        print("Distance (m):", data.get("properties", {}).get("distance_m"))

    if args.flood:
        lat, lon = args.flood.split(",")
        r = httpx.get(f"{BASE}/api/flood/point", params={"lat": lat, "lon": lon}, timeout=15)
        if r.status_code != 200:
            print(r.text, file=sys.stderr)
            sys.exit(1)
        data = r.json()
        print("Zone:", data.get("zone"))
        print("Description:", data.get("description"))

    if args.buildability:
        lat, lon = args.buildability.split(",")
        r = httpx.get(f"{BASE}/api/analysis/buildability", params={"lat": lat, "lon": lon}, timeout=15)
        if r.status_code != 200:
            print(r.text, file=sys.stderr)
            sys.exit(1)
        data = r.json()
        print("Can build:", data.get("can_build"))
        for reason in data.get("reasons", []):
            print(" -", reason)

    if not any([args.health, args.flow, args.flood, args.buildability]):
        p.print_help()


if __name__ == "__main__":
    main()
