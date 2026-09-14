---
"jarrheyd-skills": minor
---

product-review now shows a screenshot on each flow in the report. The report builder renders an `actuals` array (the several states a flow walks: filled, empty, error, after-success) alongside the single `actual`, labels each item with its `flow` name, and draws a loud placeholder plus prints a warning for any visual item that reached its screen but carries no screenshot, so a flow without its shot is visible instead of silently dropped. The evidence and verdict phases now require a screenshot per reachable flow and document saving all flow shots into the review folder. Only a purely behavioral expectation may lean on `code` alone.
