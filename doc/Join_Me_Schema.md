**Join Me**

Project Schema: Overview, Features and Requirements

Python Project, Week 1: Fundamentals Application  |  Front end and deployment: Streamlit

# **1\. Overview**

Join Me is a small web app for quick, short plans. If you plan to do something quick, such as having lunch, studying, working on a task, or discussing something, you post it in the app with the time and place. Anyone interested taps Join, and everyone can see who is coming. Nobody needs to ask around in the group chat.

**Short-term by design.** Each plan only lasts for that break or session. It disappears automatically depending on what the user inputs, so the list always shows what is happening now.

# **2\. Features**

| Feature | Description |
| :---- | :---- |
| **Browse live plans** | A list of all active plans, soonest first, so the user sees what is happening now. |
| **Plan details** | Title, category, place, start time, time left, host, description, and the list of people joined. |
| **Create a plan** | Post a plan with title, category (Lunch, Study, Work, Discussion, Other), place, start time (now or later today), description, and host name. |
| **Search** | Find a plan by keyword in the title, place, or category. |
| **Join a plan** | Tap Join with a display name. Duplicate joins are blocked, and the participant count updates immediately. |
| **Leave a plan** | Remove yourself from a plan you joined. |
| **See who is coming** | Attendee names and the total count shown on every plan. |
| **Cancel a plan** | The host can cancel their own plan before it expires. |
| **Auto-expiry** | It disappears automatically depending on what the user inputs |

# **3\. User Requirements**

**As a user, I should be able to do the following:**

* Browse the plans that are active right now.

* View the details of a plan (title, category, place, start time, time left, host, description, attendees).

* Search for a plan by keyword.

* Create a new plan with a time and place.

* Join a plan and see my name appear in its attendee list.

* Leave a plan I joined.

* See how many people are coming and how many have joined.

* Cancel a plan that I created.

* Trust that It disappears automatically depending on what the user inputs.

# **4\. Programming Concepts (Week 1 Requirements)**

| Concept | Requirement | How Join Me uses it |
| :---- | :---- | :---- |
| **Data types** | At least 3 types | str (title, place, names), int (participant count, minutes left), bool (is the plan active), list (attendees), dict (a plan). |
| **Collections** | list, tuple, set, or dict | A dict of plans keyed by plan ID. Each plan holds a list of attendees. |
| **Conditions** | if, elif, else | Check whether a plan is active, whether the user already joined, whether the user is the host, and whether input is empty. |
| **Loops** | At least one for or while | for loops to display plans and attendees and to search through plans. |
| **Functions** | One custom function with parameters and a return value | is\_active(plan) returns a bool. search\_plans(keyword) returns a list. minutes\_left(plan) returns an int. |
| **Lambda** | One lambda function | Sort plans by start time: sorted(plans, key=lambda p: p\["start"\]). |
| **User input** | input() | Streamlit equivalents: st.text\_input(), st.selectbox(), st.time\_input(), st.button(). |
| **Output** | print() | Streamlit equivalents: st.write() and other display calls, shown clearly in cards and tables. |

# **5\. Data Model**

Each plan is stored as a dictionary:

| Field | Type | Example / note |
| :---- | :---- | :---- |
| **title** | str | "Lunch at the cafeteria" |
| **category** | str | "Lunch" (one of Lunch, Study, Work, Discussion, Other) |
| **place** | str | "Building 4, ground floor" |
| **start** | datetime | The start time. The expiry time |
| **description** | str | Short optional note. |
| **host** | str | Display name of the creator. |
| **attendees** | list | \["Sara", "Lama"\]. The host is included automatically. |

# **6\. Technical Notes and Scope**

* **Shared data.** All users must see the same plans, so plans live in one shared server-side dictionary (@st.cache\_resource), not in per-browser session\_state.

* **Expiry check.** Expiry is evaluated every time the page renders. A periodic auto-refresh (about every 30 seconds) makes expired plans vanish without a click.

* **No saved data.** Everything is held in memory only. A restart clears all plans. This matches the short-term goal and avoids storing personal data.

* **No login.** Users type a display name. Host-only cancel works by matching that name, which is simple but not secure. This is acceptable at this scope.

* **Out of scope.** Accounts, notifications, maps, chat, and a database.