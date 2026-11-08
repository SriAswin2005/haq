# Builds the 2-page solution doc: python docs/solution/build.py <prototype link> <github link>
# then open docs/solution/haq.html in Chrome -> Print -> Save as PDF (A4, margins Default, no headers/footers).
import markdown, sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
md = open("haq.md", encoding="utf-8").read()
for k, v in {"RENDER_LINK": sys.argv[1], "GITHUB_LINK": sys.argv[2]}.items():
    md = md.replace(k, v)
body = markdown.markdown(md, extensions=["tables"])
css = """
@page { size: A4; margin: 13mm 15mm 12mm 15mm; }
body { font-family: 'Inter','Helvetica Neue',Arial,sans-serif; font-size: 9.3pt; line-height: 1.36; color: #1d2331; }
h1 { font-size: 15.5pt; margin: 0 0 1mm; color: #222c6e; }
.by { color: #5a6275; font-size: 8.6pt; margin: 0 0 2.5mm; }
h2 { font-size: 11pt; margin: 3.2mm 0 1.2mm; color: #222c6e; border-bottom: 0.6pt solid #d5d9e6; padding-bottom: 0.6mm; }
p { margin: 0 0 1.6mm; }
ul { margin: 0 0 1.6mm; padding-left: 4.5mm; } li { margin: 0 0 0.9mm; }
table { border-collapse: collapse; width: 100%; margin: 1mm 0 2mm; font-size: 8.6pt; }
th, td { border: 0.5pt solid #cfd4e2; padding: 0.9mm 1.6mm; text-align: left; vertical-align: top; }
th { background: #eef0f8; }
code { font-family: 'DejaVu Sans Mono',monospace; font-size: 8pt; background: #f1f2f6; padding: 0 1px; }
a { color: #2e3a8c; }
table, tr { page-break-inside: avoid; }
svg { page-break-inside: avoid; }
"""
open("haq.html", "w", encoding="utf-8").write(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>")
