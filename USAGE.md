# ROBIN HOOD Usage

## Goal

ROBIN HOOD reduces AI spend and risk by planning before it calls models. It decides what context is worth sending, which provider is sufficient, whether local compute is enough, and whether a response is good enough to trust.

## First Run

```powershell
pip install -e .
copy providers.local.json.example providers.local.json
copy robinhood.config.json.example robinhood.config.json
robinhood health --strict
robinhood provider-health --providers providers.local.json
```

## Plan Before Spending

```powershell
robinhood plan-request --config robinhood.config.json --objective "Review this repository" --estimated-input-tokens 8000
```

If `should_call` is false, do not call a model. Fix the blocker first.

## Run Locally

```powershell
robinhood run --config robinhood.config.json --objective "Summarize the repo" --path . --model llama3.1
```

For Ollama, make sure the model exists locally:

```powershell
ollama pull llama3.1
```

## Use OpenAI-Compatible Endpoints

Set environment variables named in your private `providers.local.json`, then run:

```powershell
robinhood provider-health --providers providers.local.json
robinhood plan-request --config robinhood.config.json --objective "Release review" --estimated-input-tokens 12000
robinhood run --config robinhood.config.json --objective "Release review" --path .
```

## Recover From Failures

```powershell
robinhood provider-state
robinhood provider-mark --provider ollama-local-code --status ok --reason recovered
```

Use `fail`, `rate_limited`, `quota_exhausted`, or `disabled` to keep bad routes out of future plans.
