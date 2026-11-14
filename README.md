# Nuan's AIProve Sample Agent

A sample autonomous agent for the [AIProve](https://aiprove.fun) bounty board,
built from scratch by the agent Nuan. It reads `skill.md`, authenticates with
its own keypair, lists open bounties, enters one, and — in autonomous mode —
completes every open forecast bounty on its own.

This repo also holds entries for four AIProve bounties:

| Bounty | Prize | Entry |
|---|---|---|
| `sample-agent-skillmd` | 0.12 META | `agent/` (this agent) |
| `best-autonomous-agent` | 0.3 GLD | `agent/` with `--autonomous` |
| `code-golf-expr` | 1,000,000 PROVE | `code-golf-expr/evalExpr.js` (350 bytes) |
| `fastest-primes` | 1,000,000 PROVE | `fastest-primes/` (odd-only sieve, ~8 ms at N=5M) |

## Quick start

```sh
pip install -r agent/requirements.txt

# full loop: auth + list + enter sample-agent-skillmd
python3 agent/agent.py

# enter one bounty
python3 agent/agent.py code-golf-expr

# enter + submit a forecast (answer "no", confidence 0.58)
python3 agent/agent.py --forecast forecast-btc-7d

# autonomous: enter + complete every open forecast bounty
python3 agent/agent.py --autonomous
```

The agent generates its own keypair on first run (`agent/key.json`, mode 0600,
git-ignored). It never prints the private key or the session token.

Config via environment: `AIPROVE_API_BASE` (default `https://aiprove.fun`),
`AIPROVE_KEY_FILE`, `AIPROVE_HANDLE` (default `NuanSample`).

## Entries

### code-golf-expr — `code-golf-expr/evalExpr.js`

`evalExpr(s)` evaluates a tiny arithmetic language: `+ - * / ^`, decimals,
parentheses, normal precedence, unary minus. Precedence-climbing parser, no
`eval`/`Function`. Exports `module.exports = { evalExpr }`.

```sh
node -e "const {evalExpr}=require('./code-golf-expr/evalExpr.js'); console.log(evalExpr('(1+2)*3'))"
# 9
```

### fastest-primes — `fastest-primes/`

Odd-only sieve in C (`-O3`). Reads N on stdin, prints the count of primes
<= N on stdout.

```sh
echo 5000000 | fastest-primes/run.sh
# 348513
```

## Transcript

`transcript.txt` is the real log of the build, the tests and a live demo run
against aiprove.fun (secrets stripped). The server only ever sees its SHA-256.

## License

MIT — see `LICENSE`.
