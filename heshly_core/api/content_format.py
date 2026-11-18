from __future__ import annotations
import re
import html as html_lib
import frappe

# Heuristic AI-free reformat: structure plain HTML text without rewriting.
# If site_config has openai key, we could call LLM but default is deterministic.

def _heuristic_format(html_in: str, text_in: str) -> str:
    # Reuse same logic as frontend but server-side as fallback
    # Simple: split by blank lines, detect short heading-like lines
    t = (text_in or "").strip()
    if not t:
        return html_in
    lines = [l.strip() for l in t.replace("\r\n","\n").split("\n")]
    # If input already has headings via html, preserve it
    if re.search(r"<h[2-3][\s>]", html_in, re.I):
        return html_in
    # Rebuild from text
    blocks = []
    cur = []
    for l in lines:
        if not l:
            if cur:
                blocks.append(cur); cur=[]
        else:
            cur.append(l)
    if cur:
        blocks.append(cur)
    out=[]
    for bi, b in enumerate(blocks):
        if len(b)==1 and len(b[0])<=70 and not re.search(r"[.?!]$", b[0]) and re.match(r"^[A-Z]", b[0]):
            # heading-like
            out.append(f"<h2>{html_lib.escape(b[0])}</h2>")
        elif len([x for x in b if re.match(r"^\d+[\).]\s+", x)])>=2:
            lis="".join(f"<li>{html_lib.escape(x.replace(re.match(r'^\d+[\).]\s+', x).group(0), '', 1))}</li>" if re.match(r"^\d+[\).]\s+", x) else f"<li>{html_lib.escape(x)}</li>" for x in b)
            out.append(f"<ol>{lis}</ol>")
        elif len([x for x in b if re.match(r"^[-•*]\s+", x)])>=2:
            lis="".join(f"<li>{html_lib.escape(re.sub(r'^[-•*]\s+','',x))}</li>" for x in b)
            out.append(f"<ul>{lis}</ul>")
        elif len(b)==1 and re.match(r'^["“].*[”"]$', b[0]):
            out.append(f"<blockquote><p>{html_lib.escape(b[0])}</p></blockquote>")
        else:
            joined=" ".join(b)
            out.append(f"<p>{html_lib.escape(joined)}</p>")
    html = "".join(out)
    # Demote any h1 to h2
    html = re.sub(r"<h1(\s[^>]*)?>", r"<h2\1>", html, flags=re.I)
    html = html.replace("</h1>", "</h2>")
    return html or html_in

@frappe.whitelist()
def ai_format(html: str = "", text: str = "") -> dict:
    """AI-assisted formatting: structure only, no rewriting.
    Accepts html/text, returns {html}. Deterministic heuristic today; can be upgraded to LLM.
    """
    frappe.has_permission("Heshly Blog Post", "write", throw=False)
    html = html or ""
    text = text or ""
    # Future: if openai key present, call LLM with strict instruction not to rewrite
    # For now return heuristic
    out = _heuristic_format(html, text)
    # Sanitize via same allowlist as cms.py
    from heshly_core.api.cms import _sanitize_content
    out = _sanitize_content(out)
    return {"html": out}
