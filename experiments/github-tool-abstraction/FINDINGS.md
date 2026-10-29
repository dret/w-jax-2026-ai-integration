# Findings

This file holds the whole argument of the talk, not only the parts that were
measured. Every claim carries one of three labels:

- **Observed**: seen in the traces in this folder.
- **Partly observed**: some support in the traces, with a gap.
- **Not tested**: reasoning or arithmetic, no experiment.

The experiments are small: three Claude models, two tasks, five runs per cell,
one API. They illustrate parts of the argument and do not prove it.

## What was measured

The generated server exposed 651 tools, one per GET operation in GitHub's
OpenAPI description. GitHub's own server, with its default toolsets, exposed
26. Task 1 is short (three calls at best). Task 2 is longer (about six calls
at best). Cost is the list-price estimate Claude Code reports, not what was
billed. "Paths" is the number of distinct call sequences among five runs.

| Setup | Task | Correct | Calls | Paths | Avg cost |
|-------|------|---------|-------|-------|----------|
| 651 generated tools, Sonnet | 1 | 5/5 | 3 | 1 | $0.37 |
| 651 generated tools, Sonnet | 2 | 5/5 | 11 to 14 | 5 | $0.57 |
| 651 generated tools, Haiku | 1 | 5/5 | 3 to 4 | 2 | $0.14 |
| 651 generated tools, Haiku | 2 | 5/5 | 8 to 12 | 3 | $0.16 |
| 651 generated tools, Opus | 1 | 5/5 | 4 | 2 | $0.35 |
| 651 generated tools, Opus | 2 | 5/5 | 7 to 8 | 4 | $0.56 |
| GitHub's server, Sonnet | 1 | 5/5 | 15 to 18 | 3 | $0.07 |
| GitHub's server, Sonnet | 2 | 5/5 | 6 to 8 | 3 | $0.05 |
| GitHub's server, Haiku | 1 | **3/5** | 12 to 41 | 5 | $0.01 |
| GitHub's server, Haiku | 2 | 5/5 | 6 to 7 | 2 | under $0.01 |
| GitHub's server, Opus | 1 | 5/5 | 13 to 16 | 4 | $0.14 |
| GitHub's server, Opus | 2 | 5/5 | 6 to 7 | 2 | $0.12 |

The first Sonnet run on the generated tools cost $1.32 and the following ones
$0.13, because the tool definitions get cached. That is why task 1 averages
$0.37 for Sonnet.

## The argument, step by step

### 1. An agent works against an API at runtime, with nobody to ask

Context for the talk, not an experimental claim.

### 2. Giving an agent one tool per API operation can work

**Observed.** All 30 runs with the 651 generated tools were correct, on all
three models. On the short task they took 3 or 4 calls.

### 3. It comes with side effects

**Observed**, for this tool set and these models:

- About 284,000 tokens of tool definitions go to the model with every request.
  Claude Code's usage view attributed about half of the session's usage to the
  generated server and 9% to GitHub's.
- On the longer task the generated tools cost 5 to 10 times more per run than
  GitHub's server, on every model.
- On the longer task the five runs took 3 to 5 distinct paths per model, and
  more calls than the minimum of about six.
- A stronger model needed fewer calls with the generated tools: Opus 7 to 8,
  Haiku 8 to 12, Sonnet 11 to 14 on task 2. Three models and one task.
- When blocked from a shell, Sonnet tried to use one first: one failed `Bash`
  call in each of its five task-2 runs on the generated tools.

### 4. At realistic scale this stops being an option

**Not tested** (arithmetic). The definitions came to roughly 440 tokens per
tool. At that rate about 2,300 tools fill a 1,000,000-token window on their
own. An organisation with thousands of APIs would have thousands or tens of
thousands of tools. 651 is a medium-sized collection, not a large one.

### 5. There are several techniques for working at scale

They are different approaches, not a ranking, and each one changes something
different: what the model sees, or who decides the sequence of steps.

**A curated server, written by someone else.**
**Partly observed.** GitHub's server has far fewer tools and was cheaper and
steadier on the longer task (2 or 3 distinct paths, 6 to 8 calls, on every
model). It comes for free. It is not necessarily opinionated the way you would
want. Example from the short task: the question needs the date an account was
created. That information is in the OpenAPI description (`GET /users/{username}`
returns `created_at`), but none of the server's tools return it (server
v2.0.2, image built 2026-10-08; its `search_users` tool declares no output at
all). The user search returns login, id and links, no date. It has a query language though,
with a `created:` filter. So the models asked "was this account created
between these two dates?", got a yes or no (a count of 1 or 0), and narrowed
the range until one day was left. That took 12 to 41 calls instead of one. They
usually sent two searches at once (Sonnet, first run: 16 searches in 9 rounds).
An account has only one creation date, so one search of such a pair was often
known in advance to come back empty. Haiku got two of five wrong there,
the only wrong answers in the whole grid. Tool count may not be the cause of
the cost difference, because the curated server also differs in descriptions
and in how it shapes its responses.

**Search over the tools.**
**Not tested.** Only the relevant tools reach the context, and more and more
harnesses support this. No tool-search calls appeared in these traces. How well
it works depends on the quality of the search, which is not trivial to build.

**Better descriptions on the existing API, improved automatically.**
**Not tested.** Tooling exists to take an OpenAPI description and improve it in
an automated way, and tools generated from the improved description would have
better tool descriptions as well. It is cheap because it is automated. How much
it improves quality is open. Longer descriptions also cost more tokens when all
tools are in the context, so it may combine well with search: the extra
context then lives in the search layer and does not reach the model unless the
tool is relevant.

**Skills that tell the model how to combine the tools.**
**Not tested.** The model still decides, but is given instructions.

**Declarative workflows, such as Arazzo.**
**Not tested.** The sequence of steps is described instead of left to the model.

**Code that does the task.**
**Not tested.** Written once, so that the task runs predictably and repeatably,
and exposed to the model as a single tool or API.

### 6. You find out which of these you need by watching

**Partly observed.** The binary search above is visible only in the trace; the
answers were correct. Many repeated calls to one tool with changing arguments
look like a sign of a missing capability. This could be a cheap check for any
agent and API combination, but it is one case so far.

## Limits worth saying out loud

GitHub is in every model's training data, so this is closer to a best case than
a private API would be. Five runs per cell are enough to see divergence, not to
put a number on it. Costs are estimates at list price. The model version is
recorded inside each trace.
