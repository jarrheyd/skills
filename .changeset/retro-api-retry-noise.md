---
'jarrheyd-skills': patch
---

retro: harvest drops a "continue" sent right after an API error (connection reset, timeout, overload) as network noise and only counts it; `--keep-api-retries` keeps them.
