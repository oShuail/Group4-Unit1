"""
cli_demo.py - Join Me in the console (real input() and print()).

Run it with:  python cli_demo.py
It uses the same PlanBoard as the web app, so it is also a quick way to test logic.py.

Pseudocode:
    ask for my name once
    keep showing the menu until I choose Exit
        post / show / search / join / leave / cancel
        ask with input(), call the board, print the message it returns
"""

from datetime import datetime

from logic import PlanBoard, CATEGORIES

# One line per plan. A lambda is a tiny function without a name.
line = lambda p: (f"[{p.id}] {p.title} @ {p.place} | {p.category} | {status(p)} | "
                  f"{p.count()}/{p.capacity} people: {', '.join(p.attendees)}")


def status(plan):
    """Return a short text about where the plan is in time."""
    now = datetime.now()
    phase = plan.phase(now)
    if phase == "waiting":
        return f"starts in {plan.minutes_left(now)} min"
    elif phase == "running":
        return f"running, {plan.seconds_to_end(now) // 60} min left"
    else:
        return "ended"


def ask_number(text, low, high, default):
    """Ask for a whole number between low and high. Empty answer = default.
    Keeps asking until the answer is valid, then returns it as an int."""
    while True:
        answer = input(f"{text} ({low}-{high}, Enter = {default}): ").strip()
        if answer == "":
            return default
        elif answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        else:
            print("Please type a number in the range.")


def show_plans(plans):
    """Print the plans, or a note if there are none."""
    if len(plans) == 0:
        print("No plans right now.")
    for plan in plans:
        print(line(plan))


def post_plan(board, name, keys):
    """Ask for the fields and create the plan. Remember the host key."""
    title = input("Title: ")
    print("Categories:", ", ".join(f"{i + 1}={c}" for i, c in enumerate(CATEGORIES)))
    choice = ask_number("Category number", 1, len(CATEGORIES), len(CATEGORIES))
    place = input("Place: ")
    wait = ask_number("Starts in (minutes)", 1, 60, 5)
    duration = ask_number("Lasts (minutes)", 5, 240, 60)
    capacity = ask_number("Max people", 2, 50, 10)
    description = input("Description (optional): ")

    ok, msg, plan_id, host_key = board.create_plan(title, CATEGORIES[choice - 1], place, wait,
                                                   description, name, duration, capacity)
    if ok:
        keys[plan_id] = host_key        # only the poster keeps this secret code
        print(f"{msg}: plan number {plan_id}")
    else:
        print(msg)


def main():
    board = PlanBoard()
    keys = {}                            # plan id -> host key, for the plans I posted
    name = input("Your name: ").strip()

    while True:
        board.prune_ended_plans()
        print(f"\n=== Join Me ({name}) ===")
        print("1 Post  2 Show  3 Search  4 Join  5 Leave  6 Cancel  7 Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            post_plan(board, name, keys)
        elif choice == "2":
            show_plans(board.get_active_plans())
        elif choice == "3":
            show_plans(board.search_plans(input("Keyword: ")))
        elif choice == "4":
            ok, msg = board.join_plan(ask_number("Plan number", 1, 9999, 1), name)
            print(msg)
        elif choice == "5":
            ok, msg = board.leave_plan(ask_number("Plan number", 1, 9999, 1), name)
            print(msg)
        elif choice == "6":
            plan_id = ask_number("Plan number", 1, 9999, 1)
            ok, msg = board.cancel_plan(plan_id, name, keys.get(plan_id, ""))
            print(msg)
        elif choice == "7":
            print("Bye!")
            break
        else:
            print("Choose a number from 1 to 7.")


main()
