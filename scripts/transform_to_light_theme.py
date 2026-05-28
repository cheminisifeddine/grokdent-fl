#!/usr/bin/env python3
"""
Transform all SaaS HTML pages to use the shared light-theme.css
instead of duplicated inline dark-theme override blocks.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path("/home/ubuntu/grokdent-fl")
FRONTEND = PROJECT_ROOT / "frontend"
PAGES = [
    "dashboard.html",
    "appointments.html",
    "billing.html",
    "settings.html",
    "analytics.html",
    "calls.html",
    "knowledge-base.html",
]

# Regex to find the large inline <style> block that starts with @import url
# and contains "Ultimate Light Mode Canvas Overrides" or similar
STYLE_BLOCK_PATTERN = re.compile(
    r"<style>\s*@import url\('https://fonts\.googleapis\.com/css2\?family=Outfit[^']+'\);.*?</style>",
    re.DOTALL | re.IGNORECASE,
)

# Alternative pattern for the style block
STYLE_BLOCK_PATTERN2 = re.compile(
    r"<style>\s*/\*\s*(?:Global Canvas|Ultimate Light Mode|Light Mode) Canvas Overrides\s*\*/.*?</style>",
    re.DOTALL | re.IGNORECASE,
)

# Pattern to find body tag with dark classes
BODY_PATTERN = re.compile(
    r'<body\s+class="([^"]*)"',
    re.IGNORECASE,
)

def remove_style_block(content: str) -> str:
    """Remove the large inline style block."""
    # Try first pattern
    new_content = STYLE_BLOCK_PATTERN.sub("", content)
    if new_content == content:
        # Try alternative
        new_content = STYLE_BLOCK_PATTERN2.sub("", new_content)
    # If still no match, try a broader approach: find the first <style>...</style>
    # that contains @import url('https://fonts.googleapis.com/css2?family=Outfit')
    if new_content == content:
        # Find style block containing the outfit font import
        idx = new_content.find("@import url('https://fonts.googleapis.com/css2?family=Outfit")
        if idx != -1:
            # Find the preceding <style>
            start = new_content.rfind("<style>", 0, idx)
            if start != -1:
                end = new_content.find("</style>", start)
                if end != -1:
                    new_content = new_content[:start] + new_content[end + len("</style>"):]
    return new_content


def add_light_theme_css(content: str) -> str:
    """Add link to light-theme.css before </head>."""
    link_tag = '  <link rel="stylesheet" href="css/light-theme.css" />\n'
    # Check if already present
    if "light-theme.css" in content:
        return content
    head_end = content.find("</head>")
    if head_end != -1:
        content = content[:head_end] + link_tag + content[head_end:]
    return content


def update_body_class(content: str) -> str:
    """Add light-theme class to body if not present."""
    def replace_body(match):
        classes = match.group(1)
        if "light-theme" in classes:
            return match.group(0)
        # Remove dark-bg classes, add light-theme
        classes = classes.replace("bg-slate-950", "").replace("bg-slate-900", "").replace("text-white", "")
        classes = classes.strip()
        if classes:
            return f'<body class="{classes} light-theme"'
        return '<body class="light-theme"'

    return BODY_PATTERN.sub(replace_body, content)


def update_main_bg(content: str) -> str:
    """Replace main container dark backgrounds with light ones."""
    # Replace common dark main container patterns
    replacements = [
        ('class="min-h-screen bg-slate-950 text-white"', 'class="min-h-screen bg-white text-slate-900 light-theme"'),
        ('class="min-h-screen bg-slate-950"', 'class="min-h-screen bg-white light-theme"'),
        ('class="flex h-screen bg-slate-950 text-white"', 'class="flex h-screen bg-white text-slate-900 light-theme"'),
        ('class="flex h-screen bg-slate-950"', 'class="flex h-screen bg-white light-theme"'),
    ]
    for old, new in replacements:
        content = content.replace(old, new)
    return content


def clean_nav(content: str) -> str:
    """Update nav to use white theme classes instead of dark."""
    # These are common nav patterns in the SaaS pages
    replacements = [
        ('bg-slate-900/80 backdrop-blur-md border-b border-white/5', 'bg-white/90 backdrop-blur-md border-b border-slate-200'),
        ('bg-slate-900/80 backdrop-blur-md border-b border-white/10', 'bg-white/90 backdrop-blur-md border-b border-slate-200'),
        ('bg-slate-950/80 backdrop-blur-md border-b border-white/5', 'bg-white/90 backdrop-blur-md border-b border-slate-200'),
        ('text-white font-display font-extrabold text-xl tracking-tight flex items-center gap-3', 'text-slate-900 font-display font-extrabold text-xl tracking-tight flex items-center gap-3'),
        ('text-slate-400 hover:text-white transition-colors', 'text-slate-600 hover:text-slate-900 transition-colors'),
        ('text-slate-400 hover:text-white', 'text-slate-600 hover:text-slate-900'),
    ]
    for old, new in replacements:
        content = content.replace(old, new)
    return content


def transform_page(path: Path) -> bool:
    """Transform a single HTML page. Returns True if modified."""
    content = path.read_text(encoding="utf-8")
    original = content

    content = remove_style_block(content)
    content = add_light_theme_css(content)
    content = update_body_class(content)
    content = update_main_bg(content)
    content = clean_nav(content)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    modified = []
    for page_name in PAGES:
        path = FRONTEND / page_name
        if not path.exists():
            print(f"SKIP: {page_name} not found")
            continue
        if transform_page(path):
            modified.append(page_name)
            print(f"MODIFIED: {page_name}")
        else:
            print(f"UNCHANGED: {page_name}")
    print(f"\nDone. Modified {len(modified)} pages: {', '.join(modified)}")


if __name__ == "__main__":
    main()
