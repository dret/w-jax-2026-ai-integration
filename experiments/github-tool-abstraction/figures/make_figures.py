#!/usr/bin/env python3
"""Draw the talk's pictures straight from the traces.

    python3 figures/make_figures.py

Writes PNGs (white background, 1600x900) next to this script. Requires
matplotlib. Every number in a picture comes from traces/, nothing is typed in.
"""
import datetime as dt
import glob
import json
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TRACES = os.path.join(HERE, "..", "traces")
OUT = HERE

GREEN, RED, DARK, GREY, LIGHT = "#78A349", "#C0392B", "#444444", "#B5B5B5", "#E6E6E6"
ANSWERS = {"task-01": "2 | vilmibm | 2009-06-24", "task-02": "16 | 4"}
MODELS = ["haiku", "sonnet", "opus"]


# ---------------------------------------------------------------- traces ----
def load_run(path):
    calls, results, answer, cost, ok = [], {}, "", 0.0, False
    order = []
    msg_of = {}  # tool_use id -> id of the assistant message that issued it (calls in one message run in parallel)
    for line in open(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        m = e.get("message")
        content = m.get("content") if isinstance(m, dict) else None
        if not isinstance(content, list):
            content = []
        if e.get("type") == "assistant":
            for b in content:
                if b.get("type") == "tool_use":
                    name = b.get("name", "?").split("__", 2)[-1]
                    calls.append(name)
                    order.append((b["id"], name, b.get("input") or {}))
                    msg_of[b["id"]] = m.get("id")
        elif e.get("type") == "user":
            for b in content:
                if b.get("type") == "tool_result":
                    results[b.get("tool_use_id")] = (str(b.get("content")), bool(b.get("is_error")))
        elif e.get("type") == "result":
            ok = not e.get("is_error")
            cost = e.get("total_cost_usd") or 0.0
            hits = re.findall(r"^ANSWER:\s*(.+)$", (e.get("result") or ""), re.M)
            answer = hits[-1].strip() if hits else ""
    return dict(calls=calls, answer=answer, cost=cost, ok=ok, order=order, results=results, msg_of=msg_of)


def load_all():
    data = {}
    for path in sorted(glob.glob(os.path.join(TRACES, "*", "task-*", "run-*.jsonl"))):
        setup = os.path.basename(os.path.dirname(os.path.dirname(path)))
        task = os.path.basename(os.path.dirname(path))
        tools, _, model = setup.partition("-")
        data.setdefault((tools, model or "sonnet", task), []).append(load_run(path))
    return data


def canvas():
    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1600)
    ax.set_ylim(900, 0)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    # transparent background, cropped to the drawing with a small margin
    import io
    from PIL import Image
    buf = io.BytesIO()
    fig.savefig(buf, dpi=100, transparent=True, format="png")
    im = Image.open(buf).convert("RGBA")
    l, t, r, b = im.getchannel("A").point(lambda a: 255 if a else 0).getbbox()
    pad = 12
    im.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, im.width), min(b + pad, im.height))).save(os.path.join(OUT, name))
    plt.close(fig)
    print("wrote", name)


# ------------------------------------------------------------ 1. the scale ---
def fig_scale():
    fig, ax = canvas()
    pitch, size = 9, 4.7   # size in points: a square of about 6.5 px on a 9 px pitch
    # our block: 31 x 21 = 651 squares
    cols, rows = 31, 21
    assert cols * rows == 651
    x0, y0 = 70, 450 - rows * pitch / 2
    xs = [x0 + c * pitch for c in range(cols) for _ in range(rows)]
    ys = [y0 + r * pitch for _ in range(cols) for r in range(rows)]
    ax.scatter(xs, ys, s=size ** 2, marker="s", color=GREEN, linewidths=0)
    # a large organisation: far more, fading out at the edges
    bc, br, bx0 = 110, 78, 500
    by0 = 450 - br * pitch / 2
    bxs, bys, al = [], [], []
    for c in range(bc):
        for r in range(br):
            fx = min(c, bc - 1 - c) / 18.0
            fy = min(r, br - 1 - r) / 12.0
            a = max(0.0, min(1.0, fx, fy))
            if a > 0.03:
                bxs.append(bx0 + c * pitch)
                bys.append(by0 + r * pitch)
                al.append(a * 0.75)
    colors = np.zeros((len(bxs), 4))
    colors[:, :3] = [0.55, 0.55, 0.55]
    colors[:, 3] = al
    ax.scatter(bxs, bys, s=size ** 2, marker="s", c=colors, linewidths=0)
    ax.text(x0 + cols * pitch / 2, y0 + rows * pitch + 50, "651 tools", ha="center",
            fontsize=30, fontweight="bold", color=DARK)
    ax.text(x0 + cols * pitch / 2, y0 + rows * pitch + 90, "this experiment", ha="center",
            fontsize=20, color=DARK)
    ax.text(bx0 + bc * pitch / 2, 450, "a large organization", ha="center", va="center",
            fontsize=40, fontweight="bold", color=DARK,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=14))
    ax.text(bx0 + bc * pitch / 2, 512, "thousands to tens of thousands of APIs and tools",
            ha="center", va="center", fontsize=24, color=DARK,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=8))
    ax.text(800, 870, "illustrative: one square is one tool", ha="center", fontsize=15, color="#888888")
    save(fig, "scale.png")


# ------------------------------------------------------ 2. all runs, dots ----
def fig_dots(data):
    fig, ax = canvas()
    rows = [(t, m) for t in ("generated", "github") for m in MODELS]
    label = {"generated": "651 tools", "github": "GitHub's 26 tools"}
    names = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus"}
    pitch, r = 78, 26
    colx = {"task-01": 700, "task-02": 1130}
    ax.text(colx["task-01"] + 2 * pitch, 150, "Task 1: short", ha="center", fontsize=28, fontweight="bold", color=DARK)
    ax.text(colx["task-02"] + 2 * pitch, 150, "Task 2: longer", ha="center", fontsize=28, fontweight="bold", color=DARK)
    wrong = total = 0
    for i, (tools, model) in enumerate(rows):
        y = 250 + i * 95 + (50 if tools == "github" else 0)
        ax.text(640, y, "%s · %s" % (label[tools], names[model]), ha="right", va="center", fontsize=24, color=DARK)
        for task, x0 in colx.items():
            runs = data.get((tools, model, task), [])
            for k in range(5):
                if k < len(runs):
                    good = runs[k]["ok"] and runs[k]["answer"] == ANSWERS[task]
                    total += 1
                    wrong += 0 if good else 1
                    col = GREEN if good else RED
                else:
                    col = LIGHT
                ax.add_patch(plt.Circle((x0 + k * pitch, y), r, color=col, lw=0))
    ax.plot([60, 1540], [255 + 3 * 95 + 3 * 95 - 285 + 25] * 2, color="#DDDDDD", lw=1.5) if False else None
    ax.text(800, 855, "%d runs, %d with a wrong answer. Green is correct." % (total, wrong),
            ha="center", fontsize=22, color="#666666")
    save(fig, "all-runs.png")


# ------------------------------------------------- 3. detours, five lanes ----
def fig_detours(data):
    fig, ax = canvas()
    kinds = {"list": DARK, "read": GREEN, "other": RED}

    def kind(name):
        if name in ("issueslist_for_repo", "list_issues", "searchissues_and_pull_requests"):
            return "list"
        if name in ("issueslist_comments", "issue_read"):
            return "read"
        return "other"

    panels = [("651 tools", data.get(("generated", "sonnet", "task-02"), []), 150),
              ("GitHub's 26 tools", data.get(("github", "sonnet", "task-02"), []), 930)]
    for title, runs, x0 in panels:
        ax.text(x0 + 300, 120, title, ha="center", fontsize=30, fontweight="bold", color=DARK)
        for i, run in enumerate(runs[:5]):
            y = 230 + i * 100
            ax.text(x0 - 25, y, "run %d" % (i + 1), ha="right", va="center", fontsize=20, color="#777777")
            for j, name in enumerate(run["calls"]):
                ax.add_patch(Rectangle((x0 + j * 44, y - 18), 36, 36, color=kinds[kind(name)], lw=0))
            ax.text(x0 + len(run["calls"]) * 44 + 8, y, "%d" % len(run["calls"]), va="center",
                    fontsize=20, color="#777777")
    lx = 300
    for lbl, col in (("listing issues", DARK), ("reading comments", GREEN), ("tried a shell (failed)", RED)):
        ax.add_patch(Rectangle((lx, 790), 30, 30, color=col, lw=0))
        ax.text(lx + 42, 806, lbl, va="center", fontsize=21, color=DARK)
        lx += 330 if lbl != "reading comments" else 360
    ax.text(800, 870, "task 2, Sonnet, five runs each; one square is one tool call", ha="center",
            fontsize=17, color="#888888")
    save(fig, "detours.png")


# ----------------------------------------------------------- 4. the price ----
def fig_price(data):
    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor="white")
    ax = fig.add_axes([0.08, 0.16, 0.62, 0.70])
    names = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus"}
    gen = [np.mean([r["cost"] for r in data.get(("generated", m, "task-02"), [])] or [0]) for m in MODELS]
    git = [np.mean([r["cost"] for r in data.get(("github", m, "task-02"), [])] or [0]) for m in MODELS]
    x = np.arange(len(MODELS))
    b1 = ax.bar(x - 0.2, gen, 0.38, color=GREY, label="651 tools")
    b2 = ax.bar(x + 0.2, git, 0.38, color=GREEN, label="GitHub's 26 tools")
    for bars in (b1, b2):
        for b in bars:
            v = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, "<$0.01" if v < 0.005 else "$%.2f" % v,
                    ha="center", fontsize=20, color=DARK)
    ax.set_xticks(x)
    ax.set_xticklabels([names[m] for m in MODELS], fontsize=24)
    ax.set_ylabel("cost per run, task 2 (list price)", fontsize=20)
    ax.tick_params(axis="y", labelsize=16)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=20, frameon=False, loc="upper left")
    fig.text(0.74, 0.55, "about", fontsize=22, color=DARK)
    fig.text(0.74, 0.47, "284,000", fontsize=48, fontweight="bold", color=DARK)
    fig.text(0.74, 0.41, "tokens of tool\ndefinitions on\nevery request", fontsize=22, color=DARK, va="top")
    fig.text(0.74, 0.20, "with the 651 tools", fontsize=20, color="#777777")
    save(fig, "price.png")


# ----------------------------------------------- 5. the binary search -------
def fig_binary(data):
    run = data[("github", "sonnet", "task-01")][0]
    # One row per round: searches issued in the same assistant message ran in parallel,
    # so they share a row. Reading the rows top to bottom is the real sequence.
    rounds, n_all, n_rounds = {}, 0, set()
    for tid, name, inp in run["order"]:
        if name != "search_users":
            continue
        n_all += 1
        n_rounds.add(run["msg_of"][tid])
        m = re.search(r"created:(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})", str(inp.get("query", "")))
        if not m:
            continue
        res = run["results"].get(tid, ("", False))[0]
        hit = '"total_count":1' in res.replace(" ", "")
        rounds.setdefault(run["msg_of"][tid], []).append(
            (dt.date.fromisoformat(m.group(1)), dt.date.fromisoformat(m.group(2)), hit))
    rows = list(rounds.values())
    d0, d1 = dt.date(2008, 1, 1), dt.date(2009, 12, 31)
    fig, ax = canvas()
    left, right, top, step = 70, 960, 140, 68

    def px(d):
        return left + (d - d0).days / (d1 - d0).days * (right - left)

    for yr in (2008, 2009):
        x = px(dt.date(yr, 1, 1))
        ax.plot([x, x], [top - 25, top + step * len(rows)], color="#DDDDDD", lw=1.5)
        ax.text(x + 8, top - 40, str(yr), fontsize=24, color="#777777")
    tx = px(dt.date(2009, 6, 24))
    ax.plot([tx, tx], [top - 25, top + step * len(rows)], color=DARK, lw=2, ls=(0, (4, 4)))
    for i, rnd in enumerate(rows):
        y = top + i * step
        for a, b, hit in rnd:
            w = max(px(b) - px(a), 5)
            ax.add_patch(Rectangle((px(a), y), w, 30, color=GREEN if hit else GREY, lw=0))
    tx0 = 1040
    ax.text(tx0, top + 5, "%d searches" % n_all, fontsize=40, fontweight="bold", color=DARK)
    ax.text(tx0, top + 75, "%d rounds" % len(n_rounds), fontsize=30, color=DARK, va="top")
    ax.text(tx0, top + 400, "green: account is in this range", fontsize=19, color=GREEN, va="top")
    ax.text(tx0, top + 440, "grey: it is not", fontsize=19, color="#777777", va="top")
    ax.text(tx, top + step * len(rows) + 22, "2009-06-24", ha="center", fontsize=22, fontweight="bold", color=DARK)
    save(fig, "binary-search.png")


if __name__ == "__main__":
    d = load_all()
    fig_scale()
    fig_dots(d)
    fig_detours(d)
    fig_price(d)
    fig_binary(d)
