#!/usr/bin/env python3
"""
Create an enhanced index page for GitHub Pages with test report links
"""
import os
from datetime import datetime

def create_index_html():
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartClaim Test Reports</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .report-section {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .report-link {{
            display: inline-block;
            padding: 12px 24px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 10px 10px 0;
            transition: background 0.3s;
        }}
        .report-link:hover {{
            background: #2980b9;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .status.success {{ background: #d4edda; color: #155724; }}
        .status.error {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 SmartClaim Playwright Test Reports</h1>
        
        <div class="report-section">
            <h2>Latest Test Report</h2>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <a href="report.html" class="report-link">📊 View HTML Report</a>
            {"<a href=\"screenshots/\" class=\"report-link\">📸 View Screenshots</a>" if os.path.exists("_site/screenshots") and os.listdir("_site/screenshots") else "<span class=\"report-link\" style=\"background: #95a5a6;\">📸 No Screenshots</span>"}
            {"<a href=\"playwright-report/\" class=\"report-link\">🎭 Playwright Report</a>" if os.path.exists("_site/playwright-report") else "<span class=\"report-link\" style=\"background: #95a5a6;\">🎭 No Playwright Report</span>"}
        </div>
        
        <div class="report-section">
            <h2>Test Information</h2>
            <p><strong>Environment:</strong> SmartClaim Platform</p>
            <p><strong>Browser:</strong> Chromium (Headless)</p>
            <p><strong>Test Framework:</strong> Playwright + pytest</p>
            <p><strong>Repository:</strong> <a href="{{{{ github.repository_html_url }}}}">{os.getenv('GITHUB_REPOSITORY', 'SmartClaim Testing')}</a></p>
        </div>
        
        <div class="report-section">
            <h2>Test Coverage</h2>
            <ul>
                <li>✅ User Authentication (Login)</li>
                <li>✅ File Upload & Processing</li>
                <li>✅ AI Content Generation (5 Questions)</li>
                <li>✅ UI Interaction & Validation</li>
                <li>✅ Data Cleanup</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    
    with open('_site/index.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    create_index_html()
    print("Enhanced index.html created successfully!")