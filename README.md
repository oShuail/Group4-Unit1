# مشينا | Join Me

Post a quick plan for the break. Classmates tap **Join**. Everyone sees who is coming.

**Live app:** https://meshena.streamlit.app/
**Repository:** https://github.com/oShuail/Group4-Unit1

Python Week 1 project, Group 4. Built with Python and Streamlit.

---

## The idea

Small plans fall apart in the group chat. Someone asks "anyone free for lunch?", a few people say "maybe", and nothing happens.

With Join Me, you post a short plan (lunch, studying, working on a task, a discussion, a Tuwaiq talk) with a place and a start time. Anyone interested taps **Join**, and everyone can see who is coming. Plans are short-lived on purpose: each one disappears by itself when its time is over, so the feed only shows what is happening now.

## Features

- **Name only, no account.** Type a display name and start.
- **Create a plan** with a title, category, place, "starts in N minutes", duration and number of people, with a live preview of the card.
- **Feed** of every current plan, soonest first, with your own plan pinned on top.
- **Search** by keyword and **filter** by category.
- **Join** and **leave** a plan, and see the host and everyone who joined.
- **"وصلت المكان" (I arrived):** your name turns green for everyone in the plan.
- **Cancel** a plan you host. A secret host key makes sure only the real host can cancel.
- **Auto-expiry:** plans move from *waiting* to *running* to *ended* and then disappear on their own.
- **Shared board:** every browser sees the same plans.
- Arabic, right-to-left interface.

## Rules and limits

| Rule | Value |
|---|---|
| Starts in | 1 to 60 minutes |
| Lasts | 5 to 240 minutes |
| People per plan | 2 to 12, host included |
| Joining | only while the plan is waiting |
| Host | cannot leave a plan, only cancel it |
| One plan at a time | while you host or joined a plan, you cannot create or join another |

## Run it on your computer

You need Python 3.10 or newer.

```bash
git clone https://github.com/oShuail/Group4-Unit1.git
cd Group4-Unit1
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501. Open a second browser tab with a different name to try joining your own plan.

### Console version (uses `input()` and `print()`)

```bash
python cli_demo.py
```

A text menu with the same logic: post, show, search, join, leave, cancel, "I arrived" and exit.

### Tests

```bash
python test_logic.py
```

Runs the automatic tests for `logic.py` and prints `PASS` for each one.

## Project structure

```
Group4-Unit1/
├── app.py              # Streamlit entry point: picks which screen to show
├── logic.py            # Plan and PlanBoard classes: all the rules (no Streamlit)
├── cli_demo.py         # Console version with input() and print()
├── test_logic.py       # Automatic tests for logic.py
├── requirements.txt    # streamlit
├── .streamlit/
│   └── config.toml     # Theme colors
├── ui/
│   ├── contract.py     # The one place the UI imports the logic from
│   ├── views_name.py   # Name page
│   ├── views_feed.py   # Feed: search, filter, plan cards
│   ├── views_create.py # Create form with live preview
│   ├── views_plan.py   # Plan page: countdown, people, I arrived, leave or cancel
│   ├── dialogs.py      # "Are you sure?" pop-ups
│   ├── components.py   # Shared pieces and CSS loading
│   ├── state.py        # What each browser tab remembers
│   ├── strings.py      # All Arabic text in one place
│   └── assets/         # Logo, covers and style.css
└── doc/
    ├── Code_Guide.md       # Every file, class and function explained
    ├── CONTRACT.md         # What the UI expects from logic.py
    └── Join_Me_Schema.md   # Original project schema
```

## How it works

```
Browser A ─┐
Browser B ─┼──> app.py (Streamlit) ──> ui/ ──> logic.py: ONE shared PlanBoard
Browser C ─┘
```

Streamlit gives each visitor their own copy of the page, but `app.py` creates **one** `PlanBoard` with `@st.cache_resource`. All visitors share it, which is what makes the board multiplayer. A `threading.Lock` inside `PlanBoard` lets one change happen at a time, so two people cannot take the last spot together.

## Week 1 requirements

| Requirement | Where it is used |
|---|---|
| Data types | `str` (title, names), `int` (minutes, capacity), `bool` (`is_full`, `has_joined`), `list` (attendees), `dict` (plans), `tuple` (`(ok, message)` results), `datetime` |
| Collections | `PlanBoard.plans` is a dict of plans; each plan has lists of attendees and arrived people |
| Conditions | `if / elif / else` in `Plan.phase()`, `join_plan`, `leave_plan`, `cancel_plan` and `validate_input` |
| Loops | `for` loops in `search_plans`, `prune_ended_plans` and `rename_person`; the `while` menu loop in `cli_demo.py` |
| Functions | Every `Plan` and `PlanBoard` method takes parameters and returns a value |
| Lambda | Sorting plans by start time in `get_active_plans`; the line formatter in `cli_demo.py` |
| Classes | `Plan` and `PlanBoard` in `logic.py` |
| User input | `input()` in `cli_demo.py`; Streamlit text inputs, select boxes and buttons in the web app |
| Output | `print()` in `cli_demo.py`; cards, messages and toasts in the web app |

## Known limits

- **Memory only.** Plans are not saved anywhere. Restarting or redeploying the app clears the board, which fits short-lived plans.
- **No login.** People are identified by the name they type. The host key protects cancelling, but someone typing another person's name could act as them for joining or leaving.
- **Free hosting sleeps.** After a while with no visitors, the live app shows a "wake up" button and takes about a minute to start.

## Team

Group 4: [@oShuail](https://github.com/oShuail), [@ShadenAlrshoud](https://github.com/ShadenAlrshoud), [@RaghadQi1](https://github.com/RaghadQi1), [@nnnoufff](https://github.com/nnnoufff)
