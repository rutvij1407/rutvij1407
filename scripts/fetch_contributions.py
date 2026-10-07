"""Scrape the public contribution calendar and write data/contributions.json.

Uses the same HTML fragment the GitHub profile page loads, so no token is needed.
"""
import json
import re
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "rutvij1407"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def parse_days(html):
    soup = BeautifulSoup(html, "html.parser")
    counts = {}
    for tip in soup.select("tool-tip[for]"):
        text = tip.get_text(" ", strip=True)
        m = re.match(r"([\d,]+) contributions?", text)
        counts[tip["for"]] = int(m.group(1).replace(",", "")) if m else 0

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": td["data-date"],
            "level": int(td.get("data-level", 0)),
            "count": counts.get(td.get("id"), 0),
        })
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit(f"No contribution cells found at {URL}; GitHub markup may have changed.")
    return days


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # Current streak may end yesterday: today often has no contributions yet.
    current = 0
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0:
        tail = tail[1:]
    for d in tail:
        if d["count"] == 0:
            break
        current += 1
    return current, longest


def main():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    resp.raise_for_status()
    days = parse_days(resp.text)

    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    monthly = OrderedDict()
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]

    data = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{data['total']} contributions over {len(days)} days -> {OUT.name}")


if __name__ == "__main__":
    main()
