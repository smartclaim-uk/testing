#!/usr/bin/env python3
"""
Create a simple index page for GitHub Pages with test report links and history
"""
import os
import json
from datetime import datetime

def load_report_history():
    """Load existing report history or create new"""
    history_file = '_site/report-history.json'
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return json.load(f)
    return []

def save_report_history(history):
    """Save report history"""
    with open('_site/report-history.json', 'w') as f:
        json.dump(history, f, indent=2)

def get_test_status():
    """Determine test status from report.html"""
    try:
        if os.path.exists('_site/report.html'):
            with open('_site/report.html', 'r') as f:
                content = f.read()
                if 'FAILED' in content or 'ERROR' in content:
                    return 'Failed'
                elif 'PASSED' in content or 'passed' in content:
                    return 'Passed'
        return 'Unknown'
    except:
        return 'Error'

def create_index_html():
    current_time = datetime.now()
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Load and update history
    history = load_report_history()
    
    # Add current report to history
    current_report = {
        'timestamp': timestamp,
        'date': current_time.strftime('%Y-%m-%d'),
        'time': current_time.strftime('%H:%M:%S'),
        'status': get_test_status(),
        'commit': os.getenv('GITHUB_SHA', 'unknown')[:8] if os.getenv('GITHUB_SHA') else 'local',
        'branch': os.getenv('GITHUB_REF_NAME', 'unknown')
    }
    
    # Keep only last 20 reports
    history.insert(0, current_report)
    history = history[:20]
    save_report_history(history)
    
    # Check available artifacts
    has_screenshots = os.path.exists('_site/screenshots') and os.listdir('_site/screenshots')
    has_playwright_report = os.path.exists('_site/playwright-report')
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartClaim Test Reports</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f6f8fa; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        h1 {{ color: #24292f; margin-bottom: 20px; }}
        .current-report {{ background: #f6f8fa; padding: 20px; border-radius: 6px; margin-bottom: 30px; }}
        .report-links {{ margin: 15px 0; }}
        .btn {{ display: inline-block; padding: 10px 16px; margin: 5px 10px 5px 0; background: #0969da; color: white; text-decoration: none; border-radius: 6px; font-weight: 500; }}
        .btn:hover {{ background: #0860ca; }}
        .btn.disabled {{ background: #8c959f; cursor: not-allowed; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e1e4e8; }}
        th {{ background: #f6f8fa; font-weight: 600; }}
        .status {{ padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
        .status.passed {{ background: #dcfdf4; color: #166534; }}
        .status.failed {{ background: #fee2e2; color: #dc2626; }}
        .status.unknown {{ background: #f3f4f6; color: #6b7280; }}
        .commit {{ font-family: monospace; background: #f6f8fa; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 SmartClaim Test Reports</h1>
        
        <div class="current-report">
            <h2>Latest Report</h2>
            <p><strong>Generated:</strong> {timestamp}</p>
            <p><strong>Status:</strong> <span class="status {current_report['status'].lower()}">{current_report['status']}</span></p>
            <p><strong>Commit:</strong> <span class="commit">{current_report['commit']}</span> on <strong>{current_report['branch']}</strong></p>
            
            <div class="report-links">
                <a href="report.html" class="btn">📋 View Test Report</a>
                <a href="screenshots/" class="btn{'disabled' if not has_screenshots else ''}">📸 Screenshots</a>
                <a href="playwright-report/" class="btn{'disabled' if not has_playwright_report else ''}">🎭 Playwright Report</a>
            </div>
        </div>
        
        <h2>Report History</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Commit</th>
                    <th>Branch</th>
                </tr>
            </thead>
            <tbody>'''
    
    # Add history rows
    for report in history:
        status_class = report['status'].lower()
        html_content += f'''
                <tr>
                    <td>{report['date']}</td>
                    <td>{report['time']}</td>
                    <td><span class="status {status_class}">{report['status']}</span></td>
                    <td><span class="commit">{report['commit']}</span></td>
                    <td>{report['branch']}</td>
                </tr>'''
    
    html_content += '''
            </tbody>
        </table>
    </div>
</body>
</html>'''
    
    with open('_site/index.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    create_index_html()
    print("Simple index.html with history created successfully!")