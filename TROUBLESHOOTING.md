# Troubleshooting the Mudrex API Bot

## "My key stopped working" / API key questions

- Questions like **"My key stopped working suddenly. Why?"** or **"API key not working"** are now treated as API-related (the word **key** is in the bot's strong keywords).
- If the bot still replies with a generic error, see *"Hit a snag" / generic error* below.

---

## "Hit a snag" / generic error

If the bot replies with *"Hit a snag on my side (could be temporary)..."*, it usually means the **Gemini API call failed**. Check:

1. **GEMINI_API_KEY** in `.env` – valid, not expired, and correctly set.
2. **GEMINI_MODEL** – must be a valid model name (e.g. `gemini-2.5-flash`, `gemini-2.0-flash`). `gemini-3-flash-preview` may not exist in your project; try `gemini-2.5-flash` if you see model errors.
3. **Bot logs** – the real error is logged. Inspect `bot.log` or your process logs for the exception (e.g. 401, 429, or model-not-found).

---

## "Fed a database" but bot doesn’t use it

1. **Ingest from project root**
   - Run: `python3 scripts/ingest_docs.py` from the **project root**.
   - The script loads from `docs/` and **all subdirs** (e.g. `docs/training_materials/`).

2. **Where the vector store lives**
   - Default: `./data/chroma/vectors.pkl` (relative to the **current working directory** when the bot runs).
   - Set `CHROMA_PERSIST_DIR` in `.env` if you run the bot from somewhere else, or use an absolute path so ingest and bot use the same DB.

3. **Daily job clears the store**
   - If `ENABLE_CHANGELOG_WATCHER=true`, the daily job **clears** the vector store and re-ingests only from `docs/`.
   - Anything added via `/learn` or file upload is **removed** when that job runs. To keep it, either:
     - Put the same content under `docs/` and rely on the daily ingest, or
     - Turn off the watcher: `ENABLE_CHANGELOG_WATCHER=false`.

4. **Check that docs were loaded**
   - In a group, run `/stats`. It should show `Docs: <N> chunks` with N > 0. If it’s 0, run `python3 scripts/ingest_docs.py` again and restart the bot.
