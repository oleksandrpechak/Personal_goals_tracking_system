#!/usr/bin/env python3
"""
CLI utility for the Personal Productivity Tracker.

Usage::

    python cli.py stats          — monthly & weekly opportunity stats
    python cli.py opportunities  — list today's opportunities
    python cli.py outreach       — outreach pipeline summary
    python cli.py health         — system health snapshot
    python cli.py cleanup        — delete opportunities older than 180 days

Reads the same .env configuration as the main bot.
"""

from __future__ import annotations

import argparse
import logging
import sys

from bot.analytics import get_monthly_opportunities, get_weekly_opportunities
from db.database import close_connection, get_connection
from db.queries import get_outreach_pipeline, get_today_opportunities
from db.repository import OpportunityRepository
from utils.logger import setup_logging
from utils.metrics import metrics

setup_logging(level=logging.WARNING)  # keep CLI output clean


# ── Formatters ───────────────────────────────────────────────────────────────

def _print_stats() -> None:
    """Print weekly and monthly opportunity statistics."""
    weekly = get_weekly_opportunities()
    monthly = get_monthly_opportunities()

    print("╔══════════════════════════════════════╗")
    print("║       📊 Opportunity Statistics      ║")
    print("╠══════════════════════════════════════╣")
    print("║  Weekly                              ║")
    print(f"║    Found:        {weekly['opportunities']:<20}║")
    print(f"║    Contacted:    {weekly['contacted']:<20}║")
    print(f"║    Contact rate: {weekly['contact_rate']:<19.1f}%║")
    print("╠══════════════════════════════════════╣")
    print("║  Monthly                             ║")
    print(f"║    Found:        {monthly['opportunities']:<20}║")
    print(f"║    Contacted:    {monthly['contacted']:<20}║")
    print(f"║    Contact rate: {monthly['contact_rate']:<19.1f}%║")
    print("╚══════════════════════════════════════╝")


def _print_opportunities() -> None:
    """Print today's opportunities."""
    opps = get_today_opportunities(limit=10)

    print("╔══════════════════════════════════════════════════╗")
    print("║          📰 Today's Opportunities               ║")
    print("╠══════════════════════════════════════════════════╣")

    if not opps:
        print("║  (no new opportunities today)                    ║")
    else:
        for i, opp in enumerate(opps, 1):
            title = opp["title"][:40]
            print(f"║  {i:>2}. {title:<44}║")
            url = opp["url"][:46]
            print(f"║      {url:<44}║")

    print("╚══════════════════════════════════════════════════╝")


def _print_outreach() -> None:
    """Print outreach pipeline summary."""
    pipeline = get_outreach_pipeline()

    print("╔══════════════════════════════════════╗")
    print("║        📬 Outreach Pipeline          ║")
    print("╠══════════════════════════════════════╣")
    print(f"║  Pending:    {pipeline['pending']:<23}║")
    print(f"║  Contacted:  {pipeline['contacted']:<23}║")
    print(f"║  Converted:  {pipeline['converted']:<23}║")
    print("╚══════════════════════════════════════╝")


def _print_health() -> None:
    """Print system health snapshot."""
    try:
        conn = get_connection()
        db_ok = conn is not None and not conn.closed
    except Exception:
        db_ok = False

    last = OpportunityRepository.last_created_at()
    last_text = last.strftime("%Y-%m-%d %H:%M UTC") if last else "N/A"

    m = metrics.snapshot()
    uptime_h = m["uptime_seconds"] // 3600
    uptime_m = (m["uptime_seconds"] % 3600) // 60

    print("╔══════════════════════════════════════╗")
    print("║           🏥 System Health           ║")
    print("╠══════════════════════════════════════╣")
    print(f"║  Database:       {'OK' if db_ok else 'FAIL':<19}║")
    print(f"║  Last scan:      {last_text:<19}║")
    print(f"║  Uptime:         {f'{uptime_h}h {uptime_m}m':<19}║")
    print(f"║  Msgs sent:      {m['messages_sent']:<19}║")
    print(f"║  Errors:         {m['errors']:<19}║")
    print(f"║  Jobs inserted:  {m['jobs_inserted']:<19}║")
    print("╚══════════════════════════════════════╝")


def _run_cleanup() -> None:
    """Run data cleanup — delete opportunities older than 180 days."""
    deleted = OpportunityRepository.cleanup_old(days=180)
    print(f"Cleanup complete — {deleted} old opportunities deleted.")


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    """Parse arguments and dispatch to the appropriate handler."""
    parser = argparse.ArgumentParser(
        description="Personal Productivity Tracker — CLI",
    )
    parser.add_argument(
        "command",
        choices=["stats", "opportunities", "outreach", "health", "cleanup"],
        help="The report to display.",
    )

    args = parser.parse_args()

    dispatch = {
        "stats": _print_stats,
        "opportunities": _print_opportunities,
        "outreach": _print_outreach,
        "health": _print_health,
        "cleanup": _run_cleanup,
    }

    try:
        dispatch[args.command]()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        close_connection()


if __name__ == "__main__":
    main()
