# GitHub Tool Abstraction Experiment

How reliably, and at what cost, can a model finish a task against a large API
when it is given different sets of tools? This folder holds the experiment, its
traces and the findings. The [top-level README](../../README.md) explains why.

## What Happens Here

1. GitHub's OpenAPI description is turned into an MCP server. Every read
   operation (GET) becomes one tool: 651 tools, nothing curated or renamed.
2. Claude Code is pointed at that server and given a task. The same task is run
   five times, on three models.
3. The same tasks run against GitHub's own MCP server, which exposes 26 tools
   in its default configuration.
4. For every run we record the tool calls, in order, and whether the answer is
   right. The comparison is about those traces.

Results are in [`FINDINGS.md`](FINDINGS.md), including the parts of the
argument that were not tested.

## Files

| Path | What it is |
|------|-----------|
| `FINDINGS.md` | The results, and the whole argument with a label on each step for how much evidence there is. |
| `tasks/task-01.md`, `tasks/task-02.md` | The two tasks. Task 1 is short, task 2 is longer. |
| `tasks/pin_task_02.py` | Computes the correct answer for task 2 straight from the GitHub API, without any of the tool setups. Task 1's answer was checked by hand against the API. |
| `servers/generated_server.py` | The MCP server generated from GitHub's OpenAPI description. Read-only: GET operations only. |
| `mcp/generated.json` | Starts the generated server. Reads the token from the environment. |
| `mcp/github.json` | Starts GitHub's own MCP server in Docker, read-only. |
| `run_grid.sh` | Runs both tasks five times against both setups, for the models you name. |
| `analyze.py` | Summarizes the traces: correct answers, call paths, cost. |
| `figures/make_figures.py` | Draws the talk's pictures from the traces and writes them into the slides repo. No images are kept here. |
| `inspect_calls.py` | Prints the arguments and results of each call in one trace. |
| `traces/` | One file per run. Checked in, because the traces are the evidence. |
| `spec/` | GitHub's OpenAPI description. Downloaded, not checked in. |

## Setup

You need Python 3, Claude Code (signed in), Docker for GitHub's server, and a
read-only GitHub token.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "fastmcp==4.1.4" httpx

mkdir -p spec
curl -fsSL https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json \
  -o spec/api.github.com.json

# Fine-grained token, public repositories, read-only, no extra permissions
export GITHUB_TOKEN=...
```

Check that the generated server starts and how many tools it exposes:

```bash
.venv/bin/python servers/generated_server.py < /dev/null
```

## Running

One task, one run:

```bash
claude -p "$(cat tasks/task-01.md)" \
  --mcp-config mcp/generated.json \
  --strict-mcp-config \
  --allowedTools "mcp__github-generated" \
  --tools "" \
  --model sonnet \
  --output-format stream-json --verbose \
  > traces/generated/task-01/run-1.jsonl
```

Everything, for the models you choose (skips runs that already have a trace):

```bash
./run_grid.sh haiku sonnet opus
python3 analyze.py --summary
```

What the flags are for:

- `--strict-mcp-config` makes Claude Code use only the servers in the given
  file, not your personal ones.
- `--allowedTools` pre-approves the server's tools. Without it, a
  non-interactive run blocks every call and the model reports that it has no
  data.
- `--tools ""` switches off Claude Code's built-in tools, so the model cannot
  read files or call `curl`.
- `stream-json` writes every tool call and result to the trace.

Flag names change between Claude Code versions. If one is rejected, check
`claude --help`.

If a run hits a usage limit, it leaves a trace marked `ERROR` in
`analyze.py`. Delete it before rerunning, because the script skips existing
traces.

## Things That Can Skew the Result

- **GitHub is in the training data.** The model may already know the API, so
  this is closer to a best case than a private API would be.
- **Claude Code's tool search.** With many MCP tools, Claude Code can hide them
  behind a search step, which would turn "all tools" into "tools plus search".
  No tool-search calls appeared in these traces.
- **Cost figures are list-price estimates** reported by Claude Code, not
  billed amounts.
- **Read-only on purpose.** Only GET operations are exposed and the token is
  read-only, so a run cannot change anything on GitHub.
