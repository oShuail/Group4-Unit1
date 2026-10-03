"""test_logic.py - checks the rules in logic.py. Run it with: python test_logic.py

To "wait" in a test we move the plans back in time with demo_fast_forward(minutes).
"""

from datetime import datetime

from logic import PlanBoard


def new_board():
    """A board with one plan: starts in 10 min, lasts 30 min, 3 seats, host Ali."""
    board = PlanBoard()
    ok, msg, plan_id, key = board.create_plan("Lunch", "Lunch", "Cafeteria", 10, "", "Ali", 30, 3)
    return board, board.plans[plan_id], key


def phase(plan):
    return plan.phase(datetime.now())


def test_validate():
    board = PlanBoard()
    assert board.validate_input("A", "B", "Ali", 5, 60, 10) == []
    assert board.validate_input("", "", "", 0, 1, 1) == [
        "Enter your name first", "Title is required", "Place is required",
        "Start must be between 1 and 60 minutes",
        "Duration must be between 5 and 240 minutes",
        "Capacity must be between 2 and 50"]
    assert board.validate_input("A", "B", "Ali", 61, 60, 10) != []
    assert board.validate_input("A", "B", "Ali", 5, 241, 10) != []
    assert board.validate_input("A", "B", "Ali", 5, 60, 51) != []


def test_create():
    board = PlanBoard()
    ok, msg, plan_id, key = board.create_plan(" Study ", "Nope", " Library ", 5, " hi ", " Sara ")
    plan = board.plans[plan_id]
    assert (ok, msg) == (True, "Plan posted")
    assert len(key) == 8 and plan.host_key == key
    assert (plan.title, plan.place, plan.host) == ("Study", "Library", "Sara")
    assert plan.category == "Other"                 # unknown category becomes Other
    assert plan.attendees == ["Sara"]               # the host is first
    assert board.create_plan("", "Lunch", "X", 5, "", "Ali") == (False, "Title is required", None, "")
    assert board.create_plan("B", "Work", "Y", 5, "", "Ali")[2] == plan_id + 1


def test_phases():
    board, plan, key = new_board()
    assert phase(plan) == "waiting"
    assert plan.minutes_left(datetime.now()) == 10
    board.demo_fast_forward(9.9)
    assert phase(plan) == "waiting"
    board.demo_fast_forward(0.2)                     # 10.1 min in
    assert phase(plan) == "running"
    assert plan.seconds_to_start(datetime.now()) == 0
    board.demo_fast_forward(29.8)                    # 39.9 min in
    assert phase(plan) == "running"
    assert 0 < plan.seconds_to_end(datetime.now()) <= 12
    board.demo_fast_forward(0.2)                     # 40.1 min in
    assert phase(plan) == "ended"
    assert plan.seconds_to_end(datetime.now()) == 0
    # the exact boundaries: it runs from its start time up to (not including) its end time
    assert plan.phase(plan.start_time()) == "running"
    assert plan.phase(plan.ends_at()) == "ended"


def test_listing_and_grace():
    board, plan, key = new_board()
    board.create_plan("Study", "Study", "Library", 3, "", "Sara", 20, 5)    # starts sooner
    assert [p.id for p in board.get_active_plans()] == [2, 1]               # soonest first
    board.demo_fast_forward(3.1)                     # plan 2 started 6 s ago: grace
    assert [p.id for p in board.get_active_plans()] == [2, 1]
    board.demo_fast_forward(0.2)                     # started 18 s ago: hidden
    assert [p.id for p in board.get_active_plans()] == [1]
    board.demo_fast_forward(500)
    assert board.get_active_plans() == []


def test_search():
    board, plan, key = new_board()
    board.create_plan("Python review", "Study", "Library", 5, "", "Sara")
    assert len(board.search_plans("")) == 2                                 # empty = all
    assert [p.title for p in board.search_plans("PYTHON")] == ["Python review"]
    assert [p.title for p in board.search_plans("cafeteria")] == ["Lunch"]  # place
    assert [p.title for p in board.search_plans("study")] == ["Python review"]  # category
    assert board.search_plans("zzz") == []


def test_join():
    board, plan, key = new_board()
    assert board.join_plan(1, "Sara") == (True, "You joined")
    assert board.join_plan(1, "sara") == (False, "You already joined")      # any case
    assert board.join_plan(1, "ali") == (False, "You already joined")       # the host too
    assert board.join_plan(1, "  ") == (False, "Enter your name first")
    assert board.join_plan(99, "Noor") == (False, "Plan not found or expired")
    assert board.join_plan(1, "Lama") == (True, "You joined")               # 3rd seat
    assert board.join_plan(1, "Huda") == (False, "Plan is full")
    board.demo_fast_forward(10.1)                    # now running: no more joining
    assert board.join_plan(1, "Late") == (False, "Plan not found or expired")


def test_leave():
    board, plan, key = new_board()
    board.join_plan(1, "Sara")
    assert board.leave_plan(1, "Omar") == (False, "You are not in this plan")
    assert board.leave_plan(1, "ali") == (False, "The host cannot leave, cancel instead")
    assert board.leave_plan(99, "Sara") == (False, "Plan not found or expired")
    assert board.leave_plan(1, "SARA") == (True, "You left the plan")
    assert plan.attendees == ["Ali"]
    board.join_plan(1, "Lama")
    board.demo_fast_forward(11)                      # running: leaving still works
    assert board.leave_plan(1, "Lama") == (True, "You left the plan")
    board.demo_fast_forward(40)                      # ended
    assert board.leave_plan(1, "Ali") == (False, "Plan not found or expired")


def test_cancel():
    board, plan, key = new_board()
    assert board.cancel_plan(1, "Sara", key) == (False, "Only the host can cancel")
    assert board.cancel_plan(1, "Ali", "wrongkey") == (False, "Only the host can cancel")
    assert board.cancel_plan(1, "Ali", "") == (False, "Only the host can cancel")
    assert board.cancel_plan(99, "Ali", key) == (False, "Plan not found or expired")
    assert 1 in board.plans                          # still there after every refusal
    assert board.cancel_plan(1, "ali", key) == (True, "Plan cancelled")
    assert 1 not in board.plans
    board, plan, key = new_board()
    board.demo_fast_forward(11)                      # running: the host can still cancel
    assert board.cancel_plan(1, "Ali", key) == (True, "Plan cancelled")


def test_participant_lookup():
    board, plan, key = new_board()
    board.join_plan(1, "Sara")
    assert board.get_plan_for_participant(1, "Sara") is plan
    assert board.get_plan_for_participant(1, "Omar") is None                # not in it
    assert board.get_plan_for_participant(99, "Sara") is None
    board.demo_fast_forward(11)
    assert board.get_plan_for_participant(1, "Ali") is plan                 # running counts
    board.demo_fast_forward(40)
    assert board.get_plan_for_participant(1, "Ali") is None                 # ended


def test_prune():
    board, plan, key = new_board()
    board.create_plan("Short", "Work", "Lab", 1, "", "Sara", 5, 4)          # ends after 6 min
    board.demo_fast_forward(5)
    board.prune_ended_plans()
    assert sorted(board.plans) == [1, 2]                                    # nothing ended yet
    board.demo_fast_forward(2)
    board.prune_ended_plans()
    assert sorted(board.plans) == [1]
    board.demo_fast_forward(100)
    board.prune_ended_plans()
    assert board.plans == {}


def test_rename():
    board, plan, key = new_board()
    board.join_plan(1, "Sara")
    assert board.rename_person("Ali", "  ") == (False, "Enter your name first")
    assert board.rename_person("ali", "Ahmed") == (True, "Name updated")
    assert plan.host == "Ahmed" and plan.attendees == ["Ahmed", "Sara"]
    assert board.cancel_plan(1, "Ahmed", key) == (True, "Plan cancelled")   # the key still works


def test_no_deadlock():
    """Each method takes the lock once. If one took it twice, this would freeze."""
    board, plan, key = new_board()
    board.join_plan(1, "Sara")
    board.leave_plan(1, "Sara")
    board.get_active_plans()
    board.search_plans("x")
    board.get_plan_for_participant(1, "Ali")
    board.rename_person("Ali", "Ali2")
    board.prune_ended_plans()
    board.cancel_plan(1, "Ali2", key)
    assert not board.lock.locked()


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"\nAll {len(tests)} tests passed.")
