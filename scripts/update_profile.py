"""Generate repository-hosted profile cards from public GitHub API data."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USER = "Anuragkrosuru"
ROOT = Path(__file__).resolve().parents[1]


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-cards"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    with urlopen(Request("https://api.github.com" + path, headers=headers), timeout=30) as response:
        return json.load(response)


def card(title, rows, note):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="450" height="220" viewBox="0 0 450 220" role="img">',
             f'<title>{escape(title)}</title>',
             '<rect width="450" height="220" rx="10" fill="#0d1117" stroke="#30363d"/>',
             '<g font-family="Segoe UI,Arial,sans-serif">',
             f'<text x="22" y="32" fill="#c4b5fd" font-size="19" font-weight="600">{escape(title)}</text>']
    for index, (label, value) in enumerate(rows):
        y = 62 + index * 23
        parts.append(f'<text x="22" y="{y}" fill="#c9d1d9" font-size="14">{escape(label)}</text>')
        parts.append(f'<text x="425" y="{y}" text-anchor="end" fill="#c9d1d9" font-size="14">{escape(str(value))}</text>')
    parts.append(f'<text x="22" y="203" fill="#8b949e" font-size="10">{escape(note)}</text></g></svg>')
    return "\n".join(parts) + "\n"


def main():
    user = api(f"/users/{USER}")
    repos = []
    page = 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    original = [repo for repo in repos if not repo["fork"]]
    languages = Counter()
    for repo in original:
        languages.update(api(f'/repos/{USER}/{repo["name"]}/languages'))
    total = sum(languages.values())
    top = [(name, f"{size / total:.1%}") for name, size in languages.most_common(6)]
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stats = [("Public repositories", user["public_repos"]),
             ("Stars earned", sum(repo["stargazers_count"] for repo in original)),
             ("Forks of my repositories", sum(repo["forks_count"] for repo in original)),
             ("Followers", user["followers"])]
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    # Fetch all data successfully before replacing either card.
    (assets / "github-stats.svg").write_text(card("GitHub statistics", stats, f"Public GitHub data · Updated {date} UTC"))
    (assets / "top-languages.svg").write_text(card("Most-used languages", top, f"By code bytes in public, non-fork repositories · {date} UTC"))


if __name__ == "__main__":
    main()
