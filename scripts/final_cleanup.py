#!/usr/bin/env python3
"""Final targeted cleanup for all SaaS pages."""
import re
from pathlib import Path

FRONTEND = Path("/home/ubuntu/grokdent-fl/frontend")
PAGES = [
    "dashboard.html",
    "appointments.html",
    "billing.html",
    "settings.html",
    "analytics.html",
    "calls.html",
    "knowledge-base.html",
]

# These are the most critical replacements for nav, sidebar, and app bar
REPLACEMENTS = [
    # Sidebar borders and bg
    ('border-r border-white/5', 'border-r border-slate-200'),
    ('border-r border-slate-800/80', 'border-r border-slate-200'),
    ('border-r border-slate-800', 'border-r border-slate-200'),
    ('bg-clinical-white/10 backdrop-blur-md border-r', 'bg-white border-r'),
    ('bg-clinical-white/10 backdrop-blur-md border-l', 'bg-white border-l'),
    
    # App bar / header
    ('bg-clinical-white/10 backdrop-blur-md border-b border-white/5', 'bg-white border-b border-slate-200'),
    ('bg-clinical-white/10 backdrop-blur-md border-b', 'bg-white border-b'),
    
    # Cards and panels
    ('bg-clinical-white/10 backdrop-blur-md border border-white/5', 'bg-white border border-slate-200'),
    ('bg-clinical-white/10 backdrop-blur-md border', 'bg-white border'),
    ('bg-clinical-white/10 backdrop-blur-md', 'bg-white'),
    
    # Section main backgrounds
    ('bg-slate-950', 'bg-white'),
    
    # Text colors on headings
    ('text-white font-display font-bold text-lg', 'text-slate-900 font-display font-bold text-lg'),
    ('text-white font-display font-bold text-md', 'text-slate-900 font-display font-bold text-md'),
    ('text-white font-display font-bold text-sm', 'text-slate-900 font-display font-bold text-sm'),
    ('text-white font-display font-extrabold text-2xl', 'text-slate-900 font-display font-extrabold text-2xl'),
    ('text-white font-display font-extrabold text-3xl', 'text-slate-900 font-display font-extrabold text-3xl'),
    ('text-white font-display text-2xl', 'text-slate-900 font-display text-2xl'),
    ('text-white mb-1', 'text-slate-900 mb-1'),
    ('text-white leading-none', 'text-slate-900 leading-none'),
    
    # Sidebar hover/active states
    ('hover:bg-white/10 hover:text-white', 'hover:bg-blue-50 hover:text-blue-700'),
    ('hover:bg-deep-navy hover:text-white', 'hover:bg-blue-50 hover:text-blue-700'),
    ('hover:bg-slate-900 hover:text-white', 'hover:bg-blue-50 hover:text-blue-700'),
    
    # Active nav states
    ('bg-slate-900 text-white', 'bg-blue-50 text-blue-700'),
    ('bg-slate-950 text-white', 'bg-blue-50 text-blue-700'),
    
    # Status badges
    ('bg-slate-50 border border-white/5', 'bg-slate-50 border border-slate-200'),
    ('bg-slate-50 border-b border-white/5', 'bg-slate-50 border-b border-slate-200'),
    ('bg-slate-50 border-t border-white/5', 'bg-slate-50 border-t border-slate-200'),
    
    # Deep navy panels
    ('bg-deep-navy/50', 'bg-slate-50'),
    ('bg-deep-navy/40', 'bg-slate-50'),
    ('bg-deep-navy/30', 'bg-slate-50'),
    ('bg-deep-navy flex', 'bg-white flex'),
    ('bg-deep-navy border', 'bg-white border'),
    
    # Input focus rings
    ('focus:ring-slate-950', 'focus:ring-blue-500'),
    ('focus:border-slate-950', 'focus:border-blue-500'),
    
    # Table rows
    ('divide-y divide-slate-100', 'divide-y divide-slate-100'),
    
    # Chart bars
    ('bg-slate-900 rounded-t-sm', 'bg-slate-200 rounded-t-sm'),
    ('bg-slate-950 rounded-t-sm', 'bg-slate-300 rounded-t-sm'),
    
    # Buttons with dark bg
    ('bg-slate-950 hover:bg-slate-900 text-white', 'bg-slate-900 hover:bg-slate-800 text-white'),
    ('bg-slate-950 border border-t border-white/10 text-white', 'bg-slate-900 border border-slate-200 text-white'),
    ('bg-slate-950 border border-t border-white/10', 'bg-white border border-slate-200'),
    
    # Text slate-200 on white bg
    ('text-slate-200 text-xs', 'text-slate-600 text-xs'),
    ('text-slate-200 text-sm', 'text-slate-600 text-sm'),
    ('text-slate-200 font-medium', 'text-slate-600 font-medium'),
    ('text-slate-200 font-bold', 'text-slate-700 font-bold'),
    
    # Modal overlay inline styles
    ('background:rgba(15,23,42,0.4);backdrop-filter:blur(16px)', 'background:rgba(255,255,255,0.85);backdrop-filter:blur(16px)'),
]


def transform_page(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    original = content
    
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)
    
    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    modified = []
    for page_name in PAGES:
        path = FRONTEND / page_name
        if not path.exists():
            continue
        if transform_page(path):
            modified.append(page_name)
            print(f"MODIFIED: {page_name}")
        else:
            print(f"UNCHANGED: {page_name}")
    print(f"\nDone. Modified {len(modified)} pages.")


if __name__ == "__main__":
    main()
