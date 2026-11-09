#!/usr/bin/env python3
# After a Gmail reply draft is created: the connector copies the original email's inline
# images (Outlook signatures, image001.jpg) into the draft as attachments, and he then finds
# stray images on his replies (2026-10-09). Saving the draft again with update_draft drops them
# and keeps the quoted thread, so this tells the agent to do that, once per draft.
import json, sys

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if not str(data.get('tool_name', '')).endswith('__create_draft'):
        return 0
    inp = data.get('tool_input') or {}
    if not inp.get('replyToMessageId'):
        return 0
    resp = data.get('tool_response')
    text = json.dumps(resp) if not isinstance(resp, str) else resp
    import re
    m = re.search(r'"id"\s*:\s*\\?"(r-?\d+)', text or '')
    draft = m.group(1) if m else '<the id just returned>'
    keep = ' Pass your own attachments again in that call, since it replaces them.' if inp.get('attachments') else ''
    # 10-14: the old message ordered update_draft on every reply, with or without images, which
    # clashes with assistant.md ("never update_draft a threaded reply"). The create response does
    # not list attachments, so the agent checks first and acts only on stray images.
    print(f'Check reply draft {draft} with get_draft. Only if it lists image attachments you did not add (image001.png and the like): call update_draft with draftId {draft} and the same body and htmlBody (tested 10-11, drops the images and keeps the thread), then confirm its threadId still matches the source; if it changed, trash it and create_draft again with replyToMessageId.{keep} No stray images: leave the draft alone and carry on.', file=sys.stderr)
    return 2

sys.exit(main())
