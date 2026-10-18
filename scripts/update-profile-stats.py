"""Render a dated GitHub statistics snapshot using the authenticated GitHub CLI."""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

QUERY = """
query($from: DateTime!, $to: DateTime!) {
  user(login: "dtkien-dev") {
    repositories(privacy: PUBLIC, ownerAffiliations: OWNER) { totalCount }
    followers { totalCount }
    contributionsCollection(from: $from, to: $to) {
      startedAt
      endedAt
      totalCommitContributions
      totalPullRequestContributions
    }
  }
}
"""


def render_stats(user, updated_at, compact=False):
    activity = user['contributionsCollection']
    metrics = (
        ('PUBLIC REPOS', user['repositories']['totalCount']),
        ('FOLLOWERS', user['followers']['totalCount']),
        ('COMMITS / 12 MONTHS', activity['totalCommitContributions']),
        ('PULL REQUESTS / 12 MONTHS', activity['totalPullRequestContributions']),
    )
    for _, value in metrics:
        if type(value) is not int or value < 0:
            raise ValueError('Expected non-negative integer GitHub metrics')
    start = datetime.fromisoformat(activity['startedAt'].replace('Z', '+00:00'))
    end = datetime.fromisoformat(activity['endedAt'].replace('Z', '+00:00'))
    width, height = (640, 400) if compact else (1200, 210)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">GitHub activity — dtkien-dev</title>',
           '<desc id="desc">Public repository count, followers, and GitHub commit and pull request contributions over the last 12 months.</desc>',
           '<style>rect{fill:#0D1117;stroke:#30363D}text{fill:#67C7D4;font-family:Arial,Helvetica,sans-serif}.label{fill:#E6EDF3}.meta{fill:#9DA7B3}</style>',
           f'<rect width="{width}" height="{height}" rx="16"/>',
           f'<text class="meta" x="32" y="33" font-size="14">GITHUB SNAPSHOT · UPDATED {updated_at:%Y-%m-%d %H:%M} UTC</text>']
    for index, (label, value) in enumerate(metrics):
        x = 32 + (index % 2 if compact else index) * 290
        y = 115 + (index // 2) * 120 if compact else 105
        svg.append(f'<text x="{x}" y="{y}" font-size="42" font-weight="700">{value:,}</text>')
        svg.append(f'<text class="label" x="{x}" y="{y + 34}" font-size="15">{label}</text>')
    if compact:
        svg.append(f'<text class="meta" x="32" y="335" font-size="16">Contribution window: {start:%Y-%m-%d} to {end:%Y-%m-%d}</text>')
        svg.append('<text class="meta" x="32" y="367" font-size="16">GitHub contribution rules apply</text></svg>')
    else:
        svg.append(f'<text class="meta" x="32" y="184" font-size="14">Contribution window: {start:%Y-%m-%d} to {end:%Y-%m-%d} · GitHub contribution rules apply</text></svg>')
    return '\n'.join(svg) + '\n'


if __name__ == '__main__':
    now = datetime.now(timezone.utc)
    variables = {'from': (now - timedelta(days=365)).isoformat(), 'to': now.isoformat()}
    result = subprocess.run(
        ['gh', 'api', 'graphql', '--input', '-'],
        input=json.dumps({'query': QUERY, 'variables': variables}), text=True, capture_output=True, check=True,
    )
    response = json.loads(result.stdout)
    if response.get('errors'):
        raise RuntimeError('GitHub returned GraphQL errors; keeping the previous snapshot')
    for compact, filename in ((False, 'github-stats.svg'), (True, 'github-stats-mobile.svg')):
        svg = render_stats(response['data']['user'], now, compact)
        output = Path(__file__).resolve().parents[1] / 'assets' / filename
        temporary = output.with_suffix('.svg.tmp')
        temporary.write_text(svg, encoding='utf-8', newline='\n')
        temporary.replace(output)
