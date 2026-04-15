import html as _html
from datetime import datetime, timezone


def render_dashboard(
    total_events: int,
    total_dispatches: int,
    success_count: int,
    failed_count: int,
    recent_logs: list[dict],
) -> str:
    success_rate = (
        f"{success_count / total_dispatches * 100:.1f}%"
        if total_dispatches > 0
        else "N/A"
    )

    rows = ""
    for log in recent_logs:
        status_class = "ok" if log["status"] == "success" else "err"
        rows += (
            f'<tr>'
            f'<td>{_html.escape(str(log["id"]))}</td>'
            f'<td>{_html.escape(str(log["event_id"]))}</td>'
            f'<td>{_html.escape(str(log["channel_type"]))}</td>'
            f'<td class="{status_class}">{_html.escape(log["status"].upper())}</td>'
            f'<td>{_html.escape(str(log.get("response_info") or ""))}</td>'
            f'<td>{_html.escape(str(log["dispatched_at"]))}</td>'
            f'</tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>notify-router | dashboard</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');
    :root {{
      --green:  #15ff00;
      --dim:    #0a9900;
      --bg:     #080808;
      --panel:  #0d0d0d;
      --border: #1a3300;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--green);
      font-family: 'Share Tech Mono', monospace;
      font-size: 14px;
      padding: 24px;
    }}
    h1 {{ font-family: 'VT323', monospace; font-size: 3rem; letter-spacing: 4px; margin-bottom: 4px; }}
    .subtitle {{ color: var(--dim); margin-bottom: 32px; font-size: 12px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 36px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      padding: 16px 20px;
    }}
    .card .label {{ color: var(--dim); font-size: 11px; text-transform: uppercase; letter-spacing: 2px; }}
    .card .value {{ font-family: 'VT323', monospace; font-size: 2.8rem; line-height: 1; margin-top: 4px; }}
    .card .value.rate {{ color: #00ffcc; }}
    h2 {{ font-family: 'VT323', monospace; font-size: 1.6rem; margin-bottom: 12px; letter-spacing: 2px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ color: var(--dim); text-align: left; padding: 6px 10px; font-size: 11px;
          text-transform: uppercase; border-bottom: 1px solid var(--border); }}
    td {{ padding: 6px 10px; border-bottom: 1px solid #111; font-size: 13px; white-space: nowrap; }}
    td.ok {{ color: #15ff00; }}
    td.err {{ color: #ff3c3c; }}
    .footer {{ margin-top: 40px; color: var(--dim); font-size: 11px; }}
  </style>
</head>
<body>
  <h1>&gt; NOTIFY-ROUTER</h1>
  <p class="subtitle">multi-channel notification routing engine &mdash; {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</p>

  <div class="stats">
    <div class="card">
      <div class="label">Total Events</div>
      <div class="value">{total_events}</div>
    </div>
    <div class="card">
      <div class="label">Total Dispatches</div>
      <div class="value">{total_dispatches}</div>
    </div>
    <div class="card">
      <div class="label">Successful</div>
      <div class="value">{success_count}</div>
    </div>
    <div class="card">
      <div class="label">Failed</div>
      <div class="value" style="color:#ff3c3c">{failed_count}</div>
    </div>
    <div class="card">
      <div class="label">Success Rate</div>
      <div class="value rate">{success_rate}</div>
    </div>
  </div>

  <h2>&gt; RECENT DISPATCH LOG</h2>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Event ID</th><th>Channel</th><th>Status</th><th>Info</th><th>Dispatched At</th>
      </tr>
    </thead>
    <tbody>
      {rows if rows else '<tr><td colspan="6" style="color:#333;text-align:center">— no dispatches yet —</td></tr>'}
    </tbody>
  </table>

  <p class="footer">notify-router &mdash; SOLID event-driven architecture</p>
</body>
</html>"""
