#!/usr/bin/env python3
"""
Generate a feature-rich GitHub Pages dashboard for SmartClaim test reports.
- Trend chart (inline SVG)
- Per-test pass/fail badges
- Screenshot gallery with lightbox
- Video player section
- History table with links to archived runs
- Dark mode support
"""
import html
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

SITE_DIR = "_site"
HISTORY_FILE = f"{SITE_DIR}/report-history.json"
MAX_HISTORY = 30
MAX_VIDEO_RUNS = 5  # only keep videos for last N runs to save space


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def parse_junit_xml(path):
    """Parse JUnit XML for per-test results."""
    tests = []
    total_duration = 0
    if not os.path.exists(path):
        return tests, total_duration
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        for tc in root.iter("testcase"):
            name = tc.get("name", "unknown")
            duration = float(tc.get("time", 0))
            total_duration += duration
            result = "passed"
            message = ""
            if tc.find("failure") is not None:
                result = "failed"
                message = tc.find("failure").get("message", "")[:200]
            elif tc.find("error") is not None:
                result = "error"
                message = tc.find("error").get("message", "")[:200]
            elif tc.find("skipped") is not None:
                result = "skipped"
            tests.append(
                {
                    "name": name,
                    "result": result,
                    "duration": round(duration, 1),
                    "message": message,
                }
            )
    except Exception as e:
        print(f"Error parsing JUnit XML: {e}")
    return tests, round(total_duration, 1)


def parse_report_html_fallback(path):
    """Fallback: parse data-jsonblob from pytest-html report."""
    tests = []
    if not os.path.exists(path):
        return tests
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'data-jsonblob="([^"]+)"', content)
        if match:
            blob = html.unescape(match.group(1))
            data = json.loads(blob)
            for test_id, runs in data.get("tests", {}).items():
                if runs:
                    r = runs[-1]
                    name = test_id.split("::")[-1] if "::" in test_id else test_id
                    result = r.get("result", "unknown").lower()
                    tests.append({"name": name, "result": result, "duration": 0, "message": ""})
    except Exception as e:
        print(f"Error parsing report.html fallback: {e}")
    return tests


def catalog_media(run_dir):
    screenshots = sorted(Path(f"{run_dir}/screenshots").glob("*.png")) if Path(f"{run_dir}/screenshots").exists() else []
    videos = sorted(Path(f"{run_dir}/videos").glob("*.webm")) if Path(f"{run_dir}/videos").exists() else []
    return [s.name for s in screenshots], [v.name for v in videos]


def cleanup_old_runs(history):
    """Remove archived runs not in history."""
    runs_dir = Path(f"{SITE_DIR}/runs")
    if not runs_dir.exists():
        return
    keep_ids = {str(h.get("run_id", "")) for h in history}
    for d in runs_dir.iterdir():
        if d.is_dir() and d.name not in keep_ids:
            shutil.rmtree(d, ignore_errors=True)
            print(f"Cleaned up old run: {d.name}")

    # Remove videos from runs older than MAX_VIDEO_RUNS
    recent_ids = [str(h.get("run_id", "")) for h in history[:MAX_VIDEO_RUNS]]
    for d in runs_dir.iterdir():
        if d.is_dir() and d.name not in recent_ids:
            videos_dir = d / "videos"
            if videos_dir.exists():
                shutil.rmtree(videos_dir, ignore_errors=True)


def format_duration(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m"


def generate_trend_svg(history):
    """Generate an inline SVG bar chart for pass/fail trend."""
    runs = list(reversed(history[:MAX_HISTORY]))
    if not runs:
        return '<p style="color:var(--text-muted);font-size:13px;">No history yet.</p>'

    w, h = 700, 180
    pad_left, pad_bottom, pad_top = 40, 30, 10
    chart_w = w - pad_left - 10
    chart_h = h - pad_bottom - pad_top
    n = len(runs)
    bar_w = max(4, min(20, (chart_w - n) // max(n, 1)))
    gap = max(1, (chart_w - n * bar_w) // max(n - 1, 1)) if n > 1 else 0

    svg = f'<svg viewBox="0 0 {w} {h}" style="width:100%;max-width:{w}px;height:auto;" xmlns="http://www.w3.org/2000/svg">'
    # Grid lines
    for pct in [0, 25, 50, 75, 100]:
        y = pad_top + chart_h - (pct / 100 * chart_h)
        svg += f'<line x1="{pad_left}" y1="{y}" x2="{w-10}" y2="{y}" stroke="var(--border)" stroke-dasharray="3,3"/>'
        svg += f'<text x="{pad_left-5}" y="{y+4}" text-anchor="end" fill="var(--text-muted)" font-size="10">{pct}%</text>'

    for i, run in enumerate(runs):
        total = run.get("total_tests", 0)
        passed = run.get("passed", 0)
        rate = (passed / total * 100) if total > 0 else 0
        bar_h = max(2, rate / 100 * chart_h)
        x = pad_left + i * (bar_w + gap)
        y = pad_top + chart_h - bar_h

        status = run.get("status", "unknown").lower()
        color = "var(--green)" if status == "passed" else "var(--red)" if "fail" in status else "var(--yellow)"

        svg += f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" rx="2" fill="{color}" opacity="0.85">'
        svg += f'<title>{run.get("date","?")} - {passed}/{total} passed ({rate:.0f}%)</title></rect>'

        # Date label every few bars
        if n <= 15 or i % max(1, n // 10) == 0:
            label = run.get("date", "")[-5:]  # MM-DD
            svg += f'<text x="{x + bar_w/2}" y="{h - 5}" text-anchor="middle" fill="var(--text-muted)" font-size="9">{label}</text>'

    svg += "</svg>"
    return svg


def generate_test_badges(tests):
    if not tests:
        return '<span style="color:var(--text-muted);font-size:12px;">No test data</span>'
    badges = ""
    for t in tests:
        r = t["result"]
        cls = "badge-pass" if r == "passed" else "badge-fail" if r in ("failed", "error") else "badge-skip"
        icon = "&#10003;" if r == "passed" else "&#10007;" if r in ("failed", "error") else "&#8211;"
        dur = f" ({format_duration(t['duration'])})" if t.get("duration") else ""
        title = t.get("message", "").replace('"', "&quot;") if t.get("message") else r
        badges += f'<span class="badge {cls}" title="{title}">{icon} {t["name"]}{dur}</span> '
    return badges


def generate_screenshot_gallery(run_id, screenshots):
    if not screenshots:
        return ""
    groups = {}
    for s in screenshots:
        parts = s.replace(".png", "").split("_")
        group = parts[0] if len(parts) > 1 else "general"
        # Try to get module name (draft, review, qualify)
        for mod in ("draft", "review", "qualify", "defend"):
            if mod in s:
                group = mod
                break
        groups.setdefault(group, []).append(s)

    html_out = '<div class="gallery-section"><h3>Screenshots</h3>'
    for group_name, files in sorted(groups.items()):
        html_out += f'<div class="gallery-group"><h4>{group_name.capitalize()}</h4><div class="gallery-grid">'
        for f in files:
            label = f.replace(".png", "").replace("_", " ")
            html_out += f'''<div class="gallery-item" onclick="openLightbox('runs/{run_id}/screenshots/{f}')">
                <img src="runs/{run_id}/screenshots/{f}" alt="{label}" loading="lazy"/>
                <span class="gallery-label">{label}</span>
            </div>'''
        html_out += "</div></div>"
    html_out += "</div>"
    return html_out


def generate_video_section(run_id, videos):
    if not videos:
        return ""
    html_out = '<div class="video-section"><h3>Test Videos</h3><div class="video-grid">'
    for v in videos:
        label = v.replace(".webm", "").replace("_", " ")
        html_out += f'''<div class="video-item">
            <video controls preload="metadata"><source src="runs/{run_id}/videos/{v}" type="video/webm"></video>
            <span class="video-label">{label}</span>
        </div>'''
    html_out += "</div></div>"
    return html_out


def generate_history_table(history):
    if not history:
        return '<p style="color:var(--text-muted);">No runs recorded yet.</p>'

    repo = os.getenv("GITHUB_REPOSITORY", "")
    server = os.getenv("GITHUB_SERVER_URL", "https://github.com")

    rows = ""
    for h in history:
        status = h.get("status", "unknown")
        s_cls = "passed" if status.lower() == "passed" else "failed" if "fail" in status.lower() else "neutral"
        commit = h.get("commit", "?")
        commit_link = f'<a href="{server}/{repo}/commit/{commit}" target="_blank" class="commit-link">{commit[:8]}</a>' if repo and len(commit) > 7 else f'<span class="mono">{commit}</span>'
        run_id = h.get("run_id", "")
        report_link = f'<a href="runs/{run_id}/report.html" class="btn-sm">View</a>' if run_id else ""

        mini_badges = ""
        for t in h.get("tests", []):
            r = t["result"]
            color = "var(--green)" if r == "passed" else "var(--red)" if r in ("failed", "error") else "var(--yellow)"
            mini_badges += f'<span class="dot" style="background:{color}" title="{t["name"]}: {r}"></span>'

        dur = format_duration(h["total_duration"]) if h.get("total_duration") else "-"

        rows += f"""<tr>
            <td>{h.get('date','')}<br><span class="text-sm">{h.get('time','')}</span></td>
            <td><span class="status-badge {s_cls}">{status}</span></td>
            <td>{commit_link}</td>
            <td>{h.get('branch','')}</td>
            <td class="tests-col">{mini_badges}</td>
            <td>{dur}</td>
            <td>{report_link}</td>
        </tr>"""

    return f"""<table class="history-table">
        <thead><tr>
            <th>Date</th><th>Status</th><th>Commit</th><th>Branch</th><th>Tests</th><th>Duration</th><th>Report</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>"""


def create_index_html(history, current, screenshots, videos):
    trend_svg = generate_trend_svg(history)
    test_badges = generate_test_badges(current.get("tests", []))
    screenshot_gallery = generate_screenshot_gallery(current.get("run_id", ""), screenshots)
    video_section = generate_video_section(current.get("run_id", ""), videos)
    history_table = generate_history_table(history)

    repo = os.getenv("GITHUB_REPOSITORY", "")
    server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
    commit = current.get("commit", "")
    commit_link = f'<a href="{server}/{repo}/commit/{commit}" target="_blank" class="mono">{commit[:8]}</a>' if repo and len(commit) > 7 else f'<span class="mono">{commit}</span>'

    overall_status = current.get("status", "Unknown")
    s_cls = "passed" if overall_status.lower() == "passed" else "failed" if "fail" in overall_status.lower() else "neutral"

    page = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SmartClaim Test Reports</title>
<style>
:root {{
  --bg: #f8f9fb; --bg-card: #ffffff; --text: #1a1a2e; --text-muted: #6b7280;
  --border: #e5e7eb; --green: #059669; --green-bg: #d1fae5; --red: #dc2626;
  --red-bg: #fee2e2; --yellow: #d97706; --yellow-bg: #fef3c7; --blue: #2563eb;
  --blue-bg: #dbeafe; --shadow: 0 1px 3px rgba(0,0,0,0.08);
}}
[data-theme="dark"] {{
  --bg: #0f172a; --bg-card: #1e293b; --text: #e2e8f0; --text-muted: #94a3b8;
  --border: #334155; --green: #34d399; --green-bg: #064e3b; --red: #f87171;
  --red-bg: #7f1d1d; --yellow: #fbbf24; --yellow-bg: #78350f; --blue: #60a5fa;
  --blue-bg: #1e3a5f; --shadow: 0 1px 3px rgba(0,0,0,0.3);
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:var(--bg); color:var(--text); font-size:13px; line-height:1.5; }}
.container {{ max-width:1100px; margin:0 auto; padding:16px; }}
.header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }}
.header h1 {{ font-size:20px; font-weight:700; }}
.theme-toggle {{ background:var(--bg-card); border:1px solid var(--border); border-radius:6px; padding:6px 10px; cursor:pointer; color:var(--text); font-size:16px; }}
.card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:20px; margin-bottom:16px; box-shadow:var(--shadow); }}
.card h2 {{ font-size:15px; font-weight:600; margin-bottom:12px; color:var(--text); }}
.card h3 {{ font-size:14px; font-weight:600; margin:16px 0 8px; color:var(--text); }}
.card h4 {{ font-size:12px; font-weight:600; margin:8px 0 6px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; }}
.summary-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
@media(max-width:640px) {{ .summary-grid {{ grid-template-columns:1fr; }} }}
.summary-item {{ display:flex; flex-direction:column; gap:2px; }}
.summary-label {{ font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; }}
.summary-value {{ font-size:14px; font-weight:500; }}
.status-badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.3px; }}
.status-badge.passed {{ background:var(--green-bg); color:var(--green); }}
.status-badge.failed {{ background:var(--red-bg); color:var(--red); }}
.status-badge.neutral {{ background:var(--yellow-bg); color:var(--yellow); }}
.badge {{ display:inline-block; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:500; margin:2px 3px 2px 0; white-space:nowrap; }}
.badge-pass {{ background:var(--green-bg); color:var(--green); }}
.badge-fail {{ background:var(--red-bg); color:var(--red); }}
.badge-skip {{ background:var(--yellow-bg); color:var(--yellow); }}
.mono {{ font-family:'SF Mono',Monaco,Consolas,monospace; font-size:12px; background:var(--bg); padding:1px 5px; border-radius:3px; }}
.commit-link {{ font-family:'SF Mono',Monaco,Consolas,monospace; font-size:12px; color:var(--blue); text-decoration:none; }}
.commit-link:hover {{ text-decoration:underline; }}
.btn-sm {{ display:inline-block; padding:3px 10px; background:var(--blue); color:#fff; text-decoration:none; border-radius:4px; font-size:11px; font-weight:500; }}
.btn-sm:hover {{ opacity:0.9; }}
.btn-primary {{ display:inline-block; padding:8px 16px; background:var(--blue); color:#fff; text-decoration:none; border-radius:6px; font-size:13px; font-weight:500; margin-top:10px; }}
.btn-primary:hover {{ opacity:0.9; }}
.history-table {{ width:100%; border-collapse:collapse; font-size:12px; }}
.history-table th {{ padding:8px 10px; text-align:left; background:var(--bg); font-weight:600; border-bottom:2px solid var(--border); font-size:11px; text-transform:uppercase; letter-spacing:0.3px; color:var(--text-muted); }}
.history-table td {{ padding:8px 10px; border-bottom:1px solid var(--border); vertical-align:middle; }}
.history-table tr:hover {{ background:var(--bg); }}
.text-sm {{ font-size:11px; color:var(--text-muted); }}
.dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin:0 1px; }}
.tests-col {{ white-space:nowrap; }}
.gallery-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:8px; }}
.gallery-item {{ border:1px solid var(--border); border-radius:6px; overflow:hidden; cursor:pointer; transition:transform 0.15s; }}
.gallery-item:hover {{ transform:scale(1.02); }}
.gallery-item img {{ width:100%; height:120px; object-fit:cover; display:block; }}
.gallery-label {{ display:block; padding:4px 6px; font-size:10px; color:var(--text-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.video-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:12px; }}
.video-item video {{ width:100%; border-radius:6px; background:#000; }}
.video-label {{ display:block; padding:4px 0; font-size:11px; color:var(--text-muted); }}
.lightbox {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:1000; align-items:center; justify-content:center; cursor:pointer; }}
.lightbox.active {{ display:flex; }}
.lightbox img {{ max-width:90vw; max-height:90vh; border-radius:6px; }}
.lightbox-close {{ position:fixed; top:16px; right:20px; color:#fff; font-size:28px; cursor:pointer; z-index:1001; }}
.stats-row {{ display:flex; gap:12px; flex-wrap:wrap; margin:10px 0; }}
.stat-box {{ background:var(--bg); border-radius:6px; padding:10px 14px; min-width:80px; text-align:center; }}
.stat-num {{ font-size:20px; font-weight:700; }}
.stat-label {{ font-size:10px; color:var(--text-muted); text-transform:uppercase; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>SmartClaim Test Reports</h1>
        <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode">&#9789;</button>
    </div>

    <!-- Trend Chart -->
    <div class="card">
        <h2>Pass Rate Trend</h2>
        {trend_svg}
    </div>

    <!-- Latest Run Summary -->
    <div class="card">
        <h2>Latest Run</h2>
        <div class="stats-row">
            <div class="stat-box"><div class="stat-num" style="color:var(--green)">{current.get('passed',0)}</div><div class="stat-label">Passed</div></div>
            <div class="stat-box"><div class="stat-num" style="color:var(--red)">{current.get('failed',0)}</div><div class="stat-label">Failed</div></div>
            <div class="stat-box"><div class="stat-num">{current.get('total_tests',0)}</div><div class="stat-label">Total</div></div>
            <div class="stat-box"><div class="stat-num">{format_duration(current.get('total_duration',0))}</div><div class="stat-label">Duration</div></div>
        </div>
        <div class="summary-grid" style="margin-top:12px;">
            <div class="summary-item"><span class="summary-label">Status</span><span class="summary-value"><span class="status-badge {s_cls}">{overall_status}</span></span></div>
            <div class="summary-item"><span class="summary-label">Date</span><span class="summary-value">{current.get('date','')} {current.get('time','')}</span></div>
            <div class="summary-item"><span class="summary-label">Commit</span><span class="summary-value">{commit_link}</span></div>
            <div class="summary-item"><span class="summary-label">Branch</span><span class="summary-value">{current.get('branch','')}</span></div>
        </div>
        <div style="margin-top:12px;">
            <span class="summary-label">Tests</span><br>
            {test_badges}
        </div>
        <a href="runs/{current.get('run_id','')}/report.html" class="btn-primary">View Full Report</a>
    </div>

    <!-- Screenshot Gallery -->
    <div class="card">
        <h2>Screenshots</h2>
        {screenshot_gallery if screenshot_gallery else '<p class="text-sm">No screenshots captured.</p>'}
    </div>

    <!-- Videos -->
    <div class="card">
        <h2>Videos</h2>
        {video_section if video_section else '<p class="text-sm">No videos captured.</p>'}
    </div>

    <!-- History -->
    <div class="card">
        <h2>Run History</h2>
        {history_table}
    </div>
</div>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
    <span class="lightbox-close">&times;</span>
    <img id="lightbox-img" src="" alt="Screenshot"/>
</div>

<script>
function toggleTheme(){{
    const t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
    document.documentElement.setAttribute('data-theme',t);
    localStorage.setItem('theme',t);
}}
(function(){{const t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t);
 else if(window.matchMedia('(prefers-color-scheme:dark)').matches)document.documentElement.setAttribute('data-theme','dark');}})();

function openLightbox(src){{
    document.getElementById('lightbox-img').src=src;
    document.getElementById('lightbox').classList.add('active');
}}
function closeLightbox(){{document.getElementById('lightbox').classList.remove('active');}}
document.addEventListener('keydown',function(e){{if(e.key==='Escape')closeLightbox();}});
</script>
</body>
</html>"""
    return page


def main():
    history = load_history()
    run_id = os.getenv("GITHUB_RUN_ID_VAL", str(int(datetime.now().timestamp())))
    run_dir = f"{SITE_DIR}/runs/{run_id}"
    now = datetime.utcnow()

    # Parse test results
    junit_path = f"{run_dir}/junit-results.xml"
    report_path = f"{run_dir}/report.html"
    tests, total_duration = parse_junit_xml(junit_path)
    if not tests:
        tests = parse_report_html_fallback(report_path)
        total_duration = sum(t.get("duration", 0) for t in tests)

    passed = sum(1 for t in tests if t["result"] == "passed")
    failed = sum(1 for t in tests if t["result"] in ("failed", "error"))
    total = len(tests)

    if total == 0:
        status = "No Tests"
    elif failed > 0:
        status = "Failed"
    else:
        status = "Passed"

    # Override with env var if available
    env_status = os.getenv("TEST_STATUS", "")
    if env_status == "success" and total > 0:
        status = "Passed"
    elif env_status == "failure" and total > 0:
        status = "Failed"

    screenshots, videos = catalog_media(run_dir)

    current = {
        "run_id": run_id,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "status": status,
        "commit": os.getenv("GITHUB_SHA", "local"),
        "branch": os.getenv("GITHUB_REF_NAME", "unknown"),
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "total_duration": total_duration,
        "tests": tests,
        "screenshot_count": len(screenshots),
        "video_count": len(videos),
    }

    history.insert(0, current)
    history = history[:MAX_HISTORY]
    save_history(history)
    cleanup_old_runs(history)

    index_html = create_index_html(history, current, screenshots, videos)
    with open(f"{SITE_DIR}/index.html", "w") as f:
        f.write(index_html)

    print(f"Dashboard generated: {total} tests, {passed} passed, {failed} failed")
    print(f"  Screenshots: {len(screenshots)}, Videos: {len(videos)}")
    print(f"  History: {len(history)} runs archived")


if __name__ == "__main__":
    main()
