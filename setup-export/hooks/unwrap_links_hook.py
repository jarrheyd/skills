#!/usr/bin/env python3
# Blocks drafts, sends and docs that carry Gmail's redirect links
# (https://www.google.com/url?q=REAL&source=gmail...). Those come from copying a link out of
# a received email. The block message gives the real link so the agent retries with it.
import json, re, sys
from urllib.parse import urlparse, parse_qs
try: __import__('sys').path.insert(0, __import__('os').path.expanduser('~/.claude/hooks')); __import__('hooklog').install('unwrap_links')  # fire log for the experiments (10-26)
except Exception: pass

WRAP = re.compile(r'https?://(?:www\.)?google\.com/url\?[^\s"\'<>)\]]+', re.I)

def real(u):
    q = parse_qs(urlparse(u.replace('&amp;', '&')).query)
    return (q.get('q') or q.get('url') or [None])[0]

# A Gmail draft saved as plain text gets its links rewritten into redirect links the moment
# he opens it on his phone (seen on a real draft: sent clean, wrapped 20 minutes later).
# An htmlBody with real <a href> anchors leaves Gmail nothing to rewrite.
LINK = re.compile(r'https?://\S+|\b[a-z0-9-]+\.(?:com|co|ai|app|io|ph|org|net|dev)(?:/\S*)?\b', re.I)
MAIL = re.compile(r'__(create_draft|update_draft|reply|forward|send_message|gmail_draft|gmail_send_email)$')

def plain_links(data):
    name = data.get('tool_name', '')
    ti = data.get('tool_input', {}) or {}
    if not MAIL.search(name) or 'teams' in name.lower() or 'outlook' in name.lower():
        return 0
    if name.endswith('send_message') and 'subject' not in ti:
        return 0  # a chat send, not an email
    body = ti.get('body') or ''
    html = ti.get('htmlBody') or ti.get('html_body') or ''
    if not isinstance(body, str) or html:
        return 0
    links = [m.group(0) for m in LINK.finditer(re.sub(r'\S+@\S+', ' ', body))]
    # EA retro 11-06 (rework of the 11-03 prose rule): a plain-text Gmail draft is hard-wrapped at
    # about 76 characters on send, mid-sentence (Alex Custodio reply, his 11-03 2am "why did the
    # message you drafted and i sent appear like this"). Every Gmail draft carries an htmlBody.
    if not links and 'gmail' in name.lower() and name.endswith(('create_draft', 'update_draft')) and len(body) > 76:
        print('Gmail draft with no htmlBody: Gmail hard-wraps plain text mid-sentence when he sends it. Retry with the same body plus an htmlBody (paragraphs as <p>, line breaks as <br>, links as <a href="REAL">REAL</a>).', file=sys.stderr)
        return 2
    if not links:
        return 0
    print('This email has links but no htmlBody. Gmail rewrites plain-text links into google.com/url redirects when he opens the draft. Retry with the same body plus an htmlBody where each link is <a href="REAL">REAL</a> (line breaks as <br>): ' + ', '.join(sorted(set(links))[:6]), file=sys.stderr)
    return 2

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    blob = json.dumps(data.get('tool_input', {}))
    found = {}
    for m in WRAP.finditer(blob.replace('\\u0026', '&')):
        r = real(m.group(0))
        if r:
            found[m.group(0)] = r
    if not found:
        return plain_links(data)
    lines = '\n'.join(f'- {w[:80]}... -> {r}' for w, r in found.items())
    print(f'Gmail redirect link in the text. Use the real link, in both body and htmlBody, then retry:\n{lines}', file=sys.stderr)
    return 2

sys.exit(main())
