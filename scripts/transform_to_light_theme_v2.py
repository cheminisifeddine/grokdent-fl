#!/usr/bin/env python3
"""
Comprehensive transformation of all SaaS HTML pages to the shared white clinical theme.
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

LIGHT_CSS_LINK = '  <link rel="stylesheet" href="css/light-theme.css" />\n'

# --- Pattern 1: Remove large inline <style> blocks ---
# These start with @import url('https://fonts.googleapis.com/css2?family=Outfit...')
STYLE_IMPORT_PATTERN = re.compile(
    r'<style>\s*@import\s+url\([\'"]https://fonts\.googleapis\.com/css2\?family=Outfit[^\'"]+[\'"]\);.*?</style>',
    re.DOTALL | re.IGNORECASE,
)

# --- Pattern 2: Remove any inline <style> block containing "Ultimate Light Mode" or similar ---
STYLE_COMMENT_PATTERN = re.compile(
    r'<style>\s*/\*\s*(?:Global Canvas|Ultimate Light Mode|Light Mode|DARK THEME|Dark Mode|Canvas Overrides|Monochrome|Premium white|ELITE CALL SIMULATOR).*?\*/.*?</style>',
    re.DOTALL | re.IGNORECASE,
)

# --- Pattern 3: Remove any remaining large <style> blocks (>3000 chars) that aren't needed ---
def remove_large_style_blocks(content: str) -> str:
    """Remove inline style blocks that contain dark-theme overrides."""
    # First try specific patterns
    content = STYLE_IMPORT_PATTERN.sub("", content)
    content = STYLE_COMMENT_PATTERN.sub("", content)
    
    # Also remove any <style> block containing bg-slate-950 or text-white with !important
    def style_replacer(match):
        block = match.group(0)
        # Keep small style blocks (<500 chars) — might be needed for page-specific functionality
        if len(block) < 800:
            return block
        # If it contains dark-theme indicators, remove it
        dark_indicators = ['bg-slate-950', 'bg-slate-900', 'text-white', '!important', '#0f172a']
        if any(ind in block for ind in dark_indicators):
            return ""
        return block
    
    return re.sub(r'<style>.*?</style>', style_replacer, content, flags=re.DOTALL)


# --- Pattern 4: Ensure light-theme.css is linked ---
def ensure_light_css(content: str) -> str:
    if "light-theme.css" in content:
        return content
    head_end = content.find("</head>")
    if head_end != -1:
        content = content[:head_end] + LIGHT_CSS_LINK + content[head_end:]
    return content


# --- Pattern 5: Ensure body has light-theme class ---
def ensure_body_light_theme(content: str) -> str:
    def body_replacer(match):
        full = match.group(0)
        classes = match.group(1)
        if "light-theme" in classes:
            # Clean up dark bg classes on body
            classes = classes.replace("bg-slate-950", "bg-white").replace("bg-slate-900", "bg-white")
            classes = classes.replace("text-white", "text-slate-900").replace("text-slate-200", "text-slate-700")
            return f'<body class="{classes.strip()}"'
        # Add light-theme, remove dark bg
        classes = classes.replace("bg-slate-950", "bg-white").replace("bg-slate-900", "bg-white")
        classes = classes.replace("text-white", "text-slate-900").replace("text-slate-200", "text-slate-700")
        return f'<body class="{classes.strip()} light-theme"'
    return re.sub(r'<body class="([^"]*)"', body_replacer, content, flags=re.IGNORECASE)


# --- Pattern 6: Bulk class replacements on main containers ---
CONTAINER_REPLACEMENTS = [
    # Main layout containers
    ('min-h-screen bg-slate-950 text-white', 'min-h-screen bg-white text-slate-900'),
    ('min-h-screen bg-slate-950', 'min-h-screen bg-white'),
    ('flex h-screen bg-slate-950 text-white', 'flex h-screen bg-white text-slate-900'),
    ('flex h-screen bg-slate-950', 'flex h-screen bg-white'),
    ('h-screen flex overflow-hidden', 'h-screen flex overflow-hidden bg-white'),
    
    # Nav / header
    ('bg-slate-900/80 backdrop-blur-md border-b border-white/5', 'bg-white/90 backdrop-blur-md border-b border-slate-200'),
    ('bg-slate-900/80 backdrop-blur-md border-b border-white/10', 'bg-white/90 backdrop-blur-md border-b border-slate-200'),
    ('bg-slate-950/80 backdrop-blur-md border-b border-white/5', 'bg-white/90 backdrop-blur-md border-b border-slate-200'),
    ('bg-slate-900 border-b border-slate-800', 'bg-white border-b border-slate-200'),
    
    # Text colors in nav
    ('text-white font-display font-extrabold text-xl tracking-tight flex items-center gap-3', 'text-slate-900 font-display font-extrabold text-xl tracking-tight flex items-center gap-3'),
    ('text-slate-400 hover:text-white transition-colors', 'text-slate-600 hover:text-slate-900 transition-colors'),
    ('text-slate-400 hover:text-white', 'text-slate-600 hover:text-slate-900'),
    ('text-slate-300 hover:text-white', 'text-slate-500 hover:text-slate-900'),
    
    # Sidebar
    ('bg-slate-900 border-r border-slate-800', 'bg-white border-r border-slate-200'),
    ('bg-slate-900 border-r border-white/5', 'bg-white border-r border-slate-200'),
    ('bg-slate-950 border-r border-slate-800', 'bg-white border-r border-slate-200'),
    ('bg-slate-900 w-64', 'bg-white w-64'),
    ('bg-slate-900 flex flex-col', 'bg-white flex flex-col'),
    
    # Sidebar text
    ('text-slate-400 hover:bg-slate-800 hover:text-white', 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'),
    ('text-slate-400 hover:bg-slate-800', 'text-slate-600 hover:bg-slate-50'),
    ('bg-slate-800 text-white', 'bg-blue-50 text-blue-700'),
    ('bg-slate-800 border-l-4', 'bg-blue-50 border-l-4'),
    
    # Cards / panels
    ('bg-slate-900/40 border border-slate-800/80', 'bg-white border border-slate-200'),
    ('bg-slate-900/60 border border-slate-800', 'bg-white border border-slate-200'),
    ('bg-slate-900 border border-white/5', 'bg-white border border-slate-200'),
    ('bg-slate-950 border border-white/5', 'bg-white border border-slate-200'),
    ('bg-slate-900 border border-slate-800', 'bg-white border border-slate-200'),
    ('bg-slate-800 border border-slate-700', 'bg-white border border-slate-200'),
    ('bg-slate-800 border border-white/5', 'bg-white border border-slate-200'),
    ('bg-slate-850 border border-slate-700', 'bg-white border border-slate-200'),
    
    # Tables
    ('bg-slate-900 border border-slate-800 rounded-xl overflow-hidden', 'bg-white border border-slate-200 rounded-xl overflow-hidden'),
    ('bg-slate-900/50', 'bg-slate-50'),
    
    # Modals / overlays
    ('bg-slate-900/90 backdrop-blur-md', 'bg-white/95 backdrop-blur-md'),
    ('bg-slate-950/90 backdrop-blur-md', 'bg-white/95 backdrop-blur-md'),
    
    # Inputs
    ('bg-slate-800 border border-slate-700 text-white', 'bg-white border border-slate-200 text-slate-900'),
    ('bg-slate-800 border border-slate-700 text-slate-200', 'bg-white border border-slate-200 text-slate-700'),
    ('bg-slate-800 border border-slate-700', 'bg-white border border-slate-200'),
    ('bg-slate-900 border border-slate-700 text-white', 'bg-white border border-slate-200 text-slate-900'),
    ('bg-slate-900 border border-slate-700', 'bg-white border border-slate-200'),
    
    # Buttons inside light theme (keep dark bg for primary CTA buttons but update text)
    ('bg-slate-800 hover:bg-slate-700 text-white', 'bg-slate-900 hover:bg-slate-800 text-white'),
    ('bg-slate-800 text-white', 'bg-slate-900 text-white'),
    
    # Footer
    ('bg-slate-950 border-t border-white/5', 'bg-white border-t border-slate-200'),
    ('bg-slate-950 border-t border-slate-800', 'bg-white border-t border-slate-200'),
    
    # Section backgrounds
    ('bg-slate-900/40', 'bg-slate-50'),
    ('bg-slate-900/60', 'bg-slate-50'),
    ('bg-slate-900/80', 'bg-white'),
    ('bg-slate-950/50', 'bg-slate-50'),
    ('bg-slate-950/80', 'bg-white'),
]


def bulk_replace_classes(content: str) -> str:
    for old, new in CONTAINER_REPLACEMENTS:
        content = content.replace(old, new)
    return content


# --- Pattern 7: Replace standalone bg-slate-950 on main divs ---
# Only replace bg-slate-950 when it's a main container, not inside chart JS
MAIN_CONTAINER_PATTERNS = [
    (r'class="bg-slate-950"', 'class="bg-white"'),
    (r'class="bg-slate-900 rounded-xl"', 'class="bg-white rounded-xl"'),
    (r'class="bg-slate-900 p-6"', 'class="bg-white p-6"'),
    (r'class="bg-slate-900 p-4"', 'class="bg-white p-4"'),
    (r'class="bg-slate-900 p-8"', 'class="bg-white p-8"'),
    (r'class="bg-slate-900 "', 'class="bg-white "'),
]


def replace_main_containers(content: str) -> str:
    for pattern, replacement in MAIN_CONTAINER_PATTERNS:
        content = content.replace(pattern, replacement)
    return content


# --- Pattern 8: Update nav logo to match landing page ---
def update_nav_logo(content: str) -> str:
    """Replace the nav logo text with the landing page's logo style."""
    # Find the nav logo pattern and ensure it uses text-slate-900
    content = content.replace(
        'text-white font-display font-extrabold text-xl tracking-tight flex items-center gap-3',
        'text-slate-900 font-display font-extrabold text-xl tracking-tight flex items-center gap-3'
    )
    content = content.replace(
        'text-white font-display font-extrabold text-xl',
        'text-slate-900 font-display font-extrabold text-xl'
    )
    return content


# --- Pattern 9: Fix text-slate-200 on body ---
def fix_body_text(content: str) -> str:
    """Ensure body text is dark enough for white background."""
    content = content.replace('text-slate-200 antialiased', 'text-slate-700 antialiased')
    content = content.replace('text-slate-200', 'text-slate-700')
    return content


def transform_page(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    original = content

    content = remove_large_style_blocks(content)
    content = ensure_light_css(content)
    content = ensure_body_light_theme(content)
    content = bulk_replace_classes(content)
    content = replace_main_containers(content)
    content = update_nav_logo(content)
    content = fix_body_text(content)

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
