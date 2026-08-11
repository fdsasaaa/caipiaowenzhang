# Model Provider Preflight V2.1

V2.1 can use an OpenAI-compatible provider without changing source code.

## Required compatibility

The article generator depends on all of the following:

1. Bearer API-key authentication.
2. `GET <baseURL>/models` for discovery/preflight.
3. `POST <baseURL>/responses`.
4. Responses API Structured Outputs using `text.format.type=json_schema` and `strict=true`.
5. A completed response containing `output_text` JSON that matches the requested schema.

A provider that only supports `/chat/completions` is **not** considered V2.1 production-compatible yet.

## Secrets

Never commit API keys, place them in JSON fixtures, PR text, workflow files, or command history intended for sharing.
Use environment variables or a repository/runner secret store.

```bash
export OPENAI_API_KEY='...'
export OPENAI_BASE_URL='https://provider.example/v1'
```

The provider preflight never prints the API key and redacts `sk-*` looking credentials from reported errors.

## Low-cost preflight

```bash
python scripts/model_provider_preflight_v21.py \
  --base-url "$OPENAI_BASE_URL"
```

The script first reads `/models`, prefers a model whose id looks low-cost (`nano`, `mini`, `flash`, `small`, `lite`) when no model is specified, then sends one tiny strict-schema `/responses` request.

To force a known model:

```bash
python scripts/model_provider_preflight_v21.py \
  --base-url "$OPENAI_BASE_URL" \
  --model '<model-id>'
```

A successful result requires both `responses_endpoint_ok=true` and `structured_output_ok=true`.

## Production batch with a compatible provider

After preflight succeeds:

```bash
python scripts/produce_ranked_batch_v2.py \
  --provider '<rule-provider-id>' \
  --lottery '<lottery>' \
  --play '<play>' \
  --count 1 \
  --base-url "$OPENAI_BASE_URL" \
  --model '<model-id>' \
  --output-dir runs/provider-smoke-001
```

Do not use `--record` during the first production preflight. Generation success is not approval: every model draft still passes Claim→Evidence, V2.1 editorial quality, SEO, rule, compliance, and duplicate gates before an Approved Package is produced.
