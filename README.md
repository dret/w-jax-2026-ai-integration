# What AI Agents Are Teaching Us About Integration

Material behind the talk of the same name (W-JAX Munich and API Conference
Berlin, November 2026): a small experiment on what happens when a model works
against a large API, and the argument built around it.

## The Argument

Developers used to absorb integration problems at design time, by reading
documentation and asking colleagues. Agents meet the same problems at runtime,
with neither. The talk looks at four places where they reliably stumble:
discovery, semantics, composition and errors. What an organisation can do about
it is a set of different techniques, not a single answer: tools designed by
someone else, search over the tools, improved descriptions, skills, declarative
workflows, or code. Which of them fits depends on what you find when you watch
how agents use your APIs.

The full argument is in
[`experiments/github-tool-abstraction/FINDINGS.md`](experiments/github-tool-abstraction/FINDINGS.md).
Each step there is labeled as observed, partly observed, or not tested.

## The Experiment

The same two tasks, against GitHub's REST API, with two sets of tools, on three
Claude models, five runs each:

- **651 generated tools**, one per read operation in GitHub's OpenAPI
  description, nothing curated.
- **GitHub's own MCP server**, 26 tools in its default configuration.

What the traces show, in short:

- The 651 tools worked: all 30 runs were correct. They also cost 5 to 10 times
  more per run on the longer task and produced more different call sequences.
- GitHub's server was cheaper and steadier on the longer task, but has no way to
  look up a user by name. On the short task the models worked around that with a
  binary search over date ranges, using many more calls. The smallest model did
  not reach the answer in two of five runs, after running into GitHub's search
  rate limit.

## Limits

One API that is in every model's training data, three models from one vendor,
five runs per cell and two tasks chosen by one person. The experiment
illustrates the argument and does not prove it. The tool-count arithmetic and
every technique listed above beyond GitHub's own server were not tested.

## Layout

| Path | What it is |
|------|-----------|
| `experiments/github-tool-abstraction/` | The experiment: tasks, tool servers, scripts, traces, findings. Has its own README with setup and how to rerun it. |
