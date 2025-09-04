#!/usr/bin/env python3
"""
Post-process the pytest HTML report to fix media links for screenshots and videos
"""
import os
import re
import glob
from pathlib import Path

def fix_media_links():
    """Fix media links in the HTML report"""
    report_path = 'report.html'
    
    if not os.path.exists(report_path):
        print("No report.html found to fix")
        return
    
    # Read the HTML content
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all screenshot files
    screenshot_files = glob.glob('screenshots/*.png') + glob.glob('screenshots/*.jpg')
    video_files = glob.glob('test-results/**/*.webm', recursive=True)
    
    print(f"Found {len(screenshot_files)} screenshot files")
    print(f"Found {len(video_files)} video files")
    
    # Create a mapping of test names to media files
    media_mapping = {}
    
    # Process screenshots
    for screenshot in screenshot_files:
        filename = Path(screenshot).name
        # Extract test step from filename (e.g., "01_homepage.png" -> "homepage")
        step_match = re.search(r'\d+_(.+)\.png', filename)
        if step_match:
            step_name = step_match.group(1)
            if step_name not in media_mapping:
                media_mapping[step_name] = {'screenshots': [], 'videos': []}
            media_mapping[step_name]['screenshots'].append(screenshot)
    
    # Process videos
    for video in video_files:
        # Videos are typically named by test function
        if 'draft' in video:
            if 'draft' not in media_mapping:
                media_mapping['draft'] = {'screenshots': [], 'videos': []}
            media_mapping['draft']['videos'].append(video)
    
    # Replace empty img src and video src with actual files
    def replace_media(match):
        tag_type = match.group(1)  # 'img' or 'source'
        
        # Try to find the most relevant media file
        if tag_type == 'img' and screenshot_files:
            # Use the first available screenshot
            return f'<img src="{screenshot_files[0]}" '
        elif tag_type == 'source' and video_files:
            # Use the first available video
            return f'<source src="{video_files[0]}" type="video/webm"'
        
        return match.group(0)  # Return unchanged if no media found
    
    # Replace empty src attributes
    content = re.sub(r'<(img) src=""', replace_media, content)
    content = re.sub(r'<(source) src="" type="video/mp4"', 
                     lambda m: f'<source src="{video_files[0]}" type="video/webm"' if video_files else m.group(0), 
                     content)
    
    # Add media gallery section if we have media files
    if screenshot_files or video_files:
        media_gallery = create_media_gallery(screenshot_files, video_files)
        # Insert before closing body tag
        content = content.replace('</body>', f'{media_gallery}</body>')
    
    # Write the updated content
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("HTML report media links fixed successfully!")

def create_media_gallery(screenshots, videos):
    """Create a media gallery section"""
    gallery_html = '''
<div id="media-gallery" style="margin-top: 30px; padding: 20px; border-top: 2px solid #e1e4e8;">
    <h2>Test Media Gallery</h2>
    <div style="margin: 20px 0;">
'''
    
    if screenshots:
        gallery_html += '<h3>Screenshots</h3><div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        for screenshot in screenshots:
            filename = Path(screenshot).name
            gallery_html += f'''
                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                    <img src="{screenshot}" alt="{filename}" style="max-width: 300px; max-height: 200px; display: block;">
                    <p style="margin: 5px 0 0 0; font-size: 12px; text-align: center;">{filename}</p>
                </div>
            '''
        gallery_html += '</div>'
    
    if videos:
        gallery_html += '<h3 style="margin-top: 20px;">Test Videos</h3><div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        for video in videos:
            filename = Path(video).name
            gallery_html += f'''
                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                    <video controls style="max-width: 400px; max-height: 300px;">
                        <source src="{video}" type="video/webm">
                        Your browser does not support the video tag.
                    </video>
                    <p style="margin: 5px 0 0 0; font-size: 12px; text-align: center;">{filename}</p>
                </div>
            '''
        gallery_html += '</div>'
    
    gallery_html += '''
    </div>
</div>
'''
    return gallery_html

if __name__ == "__main__":
    fix_media_links()