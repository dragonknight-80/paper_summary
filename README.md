# paper

A provider-neutral PDF summarization workflow with both watch mode and manual trigger mode.

## Structure

```text
paper/
├── raw/               # Input PDF files
├── summaries/         # Generated markdown summaries
├── summary_index.md   # Auto-generated index
├── watcher.py         # Auto mode
├── run_once.py        # Manual mode
├── config.yaml        # All configuration
└── core/              # Shared pipeline modules
```

## Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure LLM in `config.yaml`.

3. Put PDF files into `raw/`.

4. Run once manually:

```bash
python run_once.py --mode incremental
```

5. Run watch mode:

```bash
python watcher.py
```

## Provider-neutral API config

Supported providers in current implementation:

- `openai_compatible` (any OpenAI-compatible endpoint)
- `ollama`

Switch by changing:

```yaml
llm:
  provider: "openai_compatible"
```

For OpenAI-compatible endpoints, set `api_base`, `model`, and `api_key_env`.

## Notes

- Incremental mode is hash-based (`sha256`) so updates are detected reliably.
- `summary_index.md` is rebuilt automatically after each run.
