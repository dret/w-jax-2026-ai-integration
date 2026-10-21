# What AI Agents Are Teaching Us About Integration

A small field experiment behind the talk of the same name (W-JAX Munich,
November 2026; API Conference Berlin, November 2026).

Status: **design only.** Nothing is built yet. This file is written first on
purpose, so that the experiment is fixed before any results can influence it.

## Why

Having an API is not the same as being usable by an agent. Developers used to
absorb integration problems at design time, by reading documentation and asking
colleagues. Agents meet the same problems at runtime, with neither. This
repository tests one piece of that on a real API, in a way anybody can rerun.

The talk looks at four places where agents reliably stumble: discovery,
semantics, composition and errors. The traces from this experiment are where
examples of each come from.

The API is GitHub's REST API. It is large, widely known and publicly described,
and GitHub also ships its own MCP server for it, which gives us a
vendor-designed alternative to compare against.

## The Walkthrough

The experiment is a sequence of stages. Each one changes what the agent is
given and nothing else. The same tasks run at every stage.

**Stage 1: the raw operations.** Give the agent every read operation in
GitHub's OpenAPI description, as individual tools, and a goal. Then watch. Which
operations does it call? Does it finish the job? Does it take the same route
each time, or a different one? Different routes to the same answer, or to
different answers, is what we expect to see, and what we are looking for.

**Stage 2: the raw operations, plus search.** Same operations, but the agent now
has a deliberately simple search facility to find the right ones. Something off
the shelf such as BM25 or embeddings over the operation summaries. This should
already help. How much is the question.

**Stage 3: GitHub's own MCP server.** Remove the raw operations entirely and
give the agent GitHub's MCP server instead. Far fewer tools, shaped around what
people typically want to do rather than around what the API can do. GitHub
presumably knows what its users do most, so this is a case of somebody else
having done the design work for us. It is one answer to the problem, and not
claimed to be the answer.

**Stage 4: our own task-level tools.** Turn the tasks themselves into tools.
Not part of this repository yet, and whether it makes sense at all depends on
what the traces from the earlier stages show.

## Setup

- **Tasks.** Three, rising from easy to hard, where hard means more operations
  to orchestrate, with more of each result depending on the one before. Each has
  one correct answer that can be checked and does not change over time. See
  `tasks.md` once it exists.
- **Models.** The same experiment with Opus, Sonnet and Haiku, versions pinned
  and recorded per run.
- **Runs.** 20 per task, per model, per stage. That is 180 runs per stage.
- **Access.** A read-only GitHub token, and only operations that read. The agent
  cannot change anything on GitHub.
- **Conditions.** Identical prompts. A cap on turns and on tokens per run, and a
  timeout. Sampling settings left at their defaults, because the natural
  variation is part of what is being observed.

## What Gets Measured

Primarily the traces: the ordered list of tool calls each run makes. Per run we
record the answer, the number of calls, the number that failed, and tokens.

Three questions, in order of importance:

1. **Is the answer right?** Checked against answers established by hand from the
   GitHub web interface, never from any of the setups under test.
2. **Is the path stable?** Count the distinct call sequences across the 20 runs
   of a task. One means the tools decided what happened. Many means the agent
   was making it up as it went.
3. **What does it cost?** Calls and tokens.

Two more things come out of the traces. Which operations get called, and how
often, shows what agents actually use out of everything on offer. And every
run that fails or takes a different route than the others is tagged with one of
the four dimensions above, so that each has real traces behind it.

## What the Talk Takes From It

Most organisations have a lot of APIs, and that is a good starting point. What
they usually lack is a view of how agents use them: how consistently, how often,
at what cost. That view is what tells you whether a more abstract layer on top
would pay off, and how much effort it would be worth. There is no claim here to
know what that layer looks like.

The expectation is that this will keep happening, with every API and every new
agent. So the part to take away is how cheaply one can observe it, not any
particular tool design.

## What Would Count Against the Claim

Written down now so that it cannot be adjusted later.

- Stage 1 gets the right answer, with stable paths, at a cost similar to stage 3.
- Stage 2 matches stage 3.
- Stage 3 is no better than stage 1.

Any of these would be reported as found.

## Limits

One API, three models from one vendor, 20 runs per cell, and tasks chosen by one
person. GitHub's MCP server is one vendor's idea of what intent-based means.
The search in stage 2 is naive on purpose; it shows what the obvious approach
gives and says nothing about what a good one could do. This is an illustration,
not a benchmark.

## Open Decisions

- Whether the full set of read operations fits in the models' context windows
  at all, and if it does not, what size does. This is the first thing to measure
  and is itself a result.
- The three concrete tasks and their answer key.
- Which of the three models can take the full tool set. If one cannot, it
  cannot join the comparison at that size.
