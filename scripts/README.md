# Scripts

The demo scripts are kept as they were used in August 2026. Only local folder paths were redacted (see [../docs/redactions.md](../docs/redactions.md)).

Two things to know before reading them on their own:

- `score_new_cases.py` hard-codes `OPERATIONS_THRESHOLD = 0.39`. That value came from the team's earlier Colab run. The saved Week 6 notebook and the exported model use **0.40**, so notebook `06` swaps the constant when it runs the script. See [../docs/engineering_log.md](../docs/engineering_log.md).
- Comments that mention `CLAUDE.md` refer to a project-notes file that is not in this repo. Its contents are summarised in [../docs/engineering_log.md](../docs/engineering_log.md) and [../docs/limitations.md](../docs/limitations.md).

`extract_report_tables.py` was added later and reads the Final Report's tables into `results/reported/`.
