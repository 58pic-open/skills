# Troubleshooting

## Authentication errors

| Symptom | Fix |
|---|---|
| `未配置认证信息` | Run `58pic config init --api-key sk_…` or `58pic auth login` |
| `Access token 已过期，正在自动刷新…` | Automatic — wait a moment and retry |
| `Token 刷新失败，请重新执行 58pic auth login` | Run `58pic auth login` to re-authenticate |
| `OAuth token 已过期，请重新执行 58pic auth login` | Run `58pic auth login` |
| HTTP 401 from API | Token is invalid — run `58pic auth status` and re-authenticate |

Re-check after fixing:

```bash
58pic auth status -f json | jq '{loggedIn, authMethod}'
```

---

## Generation errors

### Empty `ai_id` after submit

The `same-style` submission failed upstream. Check:

```bash
# Look at code + msg in the response
echo "$RESULT" | jq '{code: .code, msg: .msg}'
```

Non-zero `code` = upstream error. Common causes:
- **Invalid model ID** — run `58pic models` to verify the ID exists
- **Missing prompt** — text-to-image requires `--prompt`
- **Credits depleted** — see [Credits depleted](#credits-depleted) below

### Status stuck at 1 or 2

If `data.status` stays at `1` or `2` for more than 10 minutes:

1. The queue may be congested. Wait and keep polling.
2. If stuck past 15 minutes, the job likely silently failed. Resubmit.

### Status is a failure code (not 1, 2, or 3)

```bash
echo "$POLL" | jq '{status: .data.status, error: .data.error_msg}'
```

Common causes:
- Content policy violation — rephrase the prompt
- Reference image inaccessible — check the URL is publicly accessible
- Model doesn't support the combination of inputs — verify with `58pic model-capabilities`

---

## Credits depleted

```bash
58pic credits -f json | jq '{balance: .data.balance}'
```

If balance is 0 or insufficient, advise the user to top up at https://ai.58pic.com.

**Tip:** Check credits before generating to avoid unexpected failures:

```bash
BALANCE=$(58pic credits -f json | jq -r '.data.balance // 0')
echo "Current balance: $BALANCE"
```

---

## Rate limits

HTTP 429 response — too many requests. Back off and retry after a few seconds.

---

## Model not found

```bash
# Verify model ID exists
58pic models -f json | jq '[.data.models[] | {id, name, category}]'
```

Model IDs are integers. If you are passing a string, ensure it's numeric:
- Valid: `-m 123`
- Also valid: `-m my_model_slug` (if the platform supports string IDs)

---

## CLI not found

```bash
# Install globally
npm install -g @58pic/cli

# Or use npx (no install needed, but slower)
npx @58pic/cli --version
```

Ensure Node.js ≥ 18 is installed:

```bash
node --version
```

---

## jq not found

`jq` is used to parse JSON output. Install it:

```bash
# macOS
brew install jq

# Ubuntu / Debian
sudo apt-get install jq

# Windows (via winget)
winget install jqlang.jq
```

Alternatively, use raw output mode and parse manually, or use `58pic <cmd> -f pretty` for human-readable output (not machine-parseable).

---

## API response codes

| `code` | Meaning |
|---|---|
| `0` | Success |
| non-zero | Error — check `.msg` for details |

HTTP status:

| HTTP | Meaning |
|---|---|
| `200` | OK |
| `401` | Unauthorized — re-authenticate |
| `403` | Forbidden — check API Key permissions |
| `429` | Rate limited — back off |
| `5xx` | Server error — retry after a few seconds |
