# عقد المنطق (logic.py)

هذا الملف يشرح بالضبط وش تحتاجه الواجهة من `logic.py`. الأسماء والرسائل بالإنجليزية **حرفياً** كما هي هنا، والواجهة هي اللي تترجمها للعربي. نسخة تجريبية جاهزة للمقارنة: `ui/dummy_logic.py`.

**قواعد عامة**
- ملف واحد `logic.py` في جذر المشروع، **بدون أي استيراد من Streamlit**.
- كل شيء في الذاكرة فقط (بدون قاعدة بيانات أو ملفات).
- نستخدم `datetime.now()` بتوقيت السيرفر، ولا نخزّن ساعة بداية بالتوقيت (فقط دقائق نسبية). لا مكتبات توقيت.
- لا تكتب أي نص عربي في المنطق.

## 1) الثوابت

```python
MIN_START_MIN = 1          # أقل وقت انتظار (دقائق)
MAX_START_MIN = 60
MIN_DURATION_MIN = 5       # أقل مدة للخطة
MAX_DURATION_MIN = 240
MIN_CAPACITY = 2           # أقل حد أقصى للمنضمين
MAX_CAPACITY = 50
EXPIRY_GRACE_SECONDS = 15  # البطاقة تبقى ظاهرة 15 ثانية بعد انتهاء الانتظار
CATEGORIES = ["Lunch", "Study", "Work", "Discussion", "Tuwaiq Talk", "Other"]
```

## 2) الكلاس Plan (خطة واحدة)

| الخاصية | النوع | ملاحظة |
|---|---|---|
| `id` | int | |
| `title` | str | |
| `category` | str | واحدة من `CATEGORIES` |
| `place` | str | |
| `description` | str | ممكن تكون فاضية |
| `host` | str | اسم صاحب الخطة |
| `starts_in_min` | int | وقت الانتظار، من 1 إلى 60 |
| `duration_min` | int | مدة الخطة بعد ما تبدأ، من 5 إلى 240 |
| `capacity` | int | أقصى عدد منضمين (يشمل المضيف) |
| `created_at` | datetime | وقت إنشاء الخطة (ساعة السيرفر) |
| `attendees` | list[str] | **المضيف دايماً أول واحد** |

الدوال:

| الدالة | ترجع | المعنى |
|---|---|---|
| `start_time()` | datetime | `created_at + starts_in_min` |
| `ends_at()` | datetime | `start_time() + duration_min` |
| `phase(now)` | str | `"waiting"` قبل البداية، `"running"` من البداية لين النهاية، `"ended"` بعدها |
| `seconds_to_start(now)` | int | ثواني للبداية (لا تنزل عن 0) |
| `seconds_to_end(now)` | int | ثواني للنهاية (لا تنزل عن 0) |
| `minutes_left(now)` | int | دقائق للبداية مقرّبة للأعلى |
| `is_active(now)` | bool | `phase(now) == "waiting"` |
| `has_joined(name)` | bool | هل الاسم في `attendees` |
| `count()` | int | عدد `attendees` |
| `is_full()` | bool | `count() >= capacity` |

## 3) الكلاس PlanBoard (لوحة واحدة مشتركة بين كل المتصفحات)

كل دالة ترجع الرسالة بالإنجليزية بالنص الحرفي المكتوب.

| الدالة | ترجع | الرسائل الممكنة |
|---|---|---|
| `validate_input(title, place, host, starts_in_min, duration_min=60, capacity=10)` | `list[str]` أخطاء، فاضية لو كل شيء صحيح | بالترتيب: `Enter your name first`، `Title is required`، `Place is required`، `Start must be between 1 and 60 minutes`، `Duration must be between 5 and 240 minutes`، `Capacity must be between 2 and 50` |
| `create_plan(title, category, place, starts_in_min, description, host, duration_min=60, capacity=10)` | `(ok, msg, plan_id)` وقت الفشل `plan_id = None` | `Plan posted` أو أول خطأ من `validate_input` |
| `get_active_plans()` | `list[Plan]` | الخطط في مرحلة `waiting` **مع** اللي بدأت قبل أقل من `EXPIRY_GRACE_SECONDS` ثانية. مرتبة بأقرب بداية (استخدم `lambda`) |
| `search_plans(keyword)` | `list[Plan]` | نفس خطط `get_active_plans()` المطابقة، بدون حساسية حروف، في `title` أو `place` أو `category` |
| `get_plan_for_participant(plan_id, name)` | `Plan` أو `None` | ترجع الخطة لو مرحلتها `waiting` أو `running` **و** الاسم في `attendees`، وإلا `None` |
| `join_plan(plan_id, name)` | `(ok, msg)` | `You joined`، `You already joined`، `Plan is full`، `Plan not found or expired`، `Enter your name first` |
| `leave_plan(plan_id, name)` | `(ok, msg)` | `You left the plan`، `The host cannot leave, cancel instead`، `You are not in this plan`، `Plan not found or expired` |
| `cancel_plan(plan_id, name)` | `(ok, msg)` | `Plan cancelled`، `Only the host can cancel`، `Plan not found or expired` |
| `prune_ended_plans()` | لا شيء | يحذف الخطط اللي مرحلتها `ended` |
| `rename_person(old, new)` | `(ok, msg)` | `Name updated` أو `Enter your name first` لو الاسم الجديد فاضي (بعد `strip()`). يغيّر الاسم في `host` وفي كل قوائم `attendees` |

**قواعد مهمة**
- `join_plan`: مسموح فقط في مرحلة `waiting`. بعد البداية يرجع `Plan not found or expired`. ترتيب الفحص: الاسم فاضي ← الخطة غير موجودة أو غير `waiting` ← منضم من قبل ← الخطة مكتملة.
- `leave_plan` و`cancel_plan`: مسموحة وقت `waiting` و`running`. بعد `ended` ترجع `Plan not found or expired`.
- المضيف: `host == name`، وهو أول واحد في `attendees` دايماً.
- `get_active_plans()` و`search_plans()` ما يرجعون أبداً خطة `ended`.
- تنظيف المسافات: `title`, `place`, `description`, `host` يتم `strip()` لهم عند الإنشاء.

## 4) كيف تتأكدون أن منطقكم يطابق العقد

شغّلوا `tests/test_dummy_logic.py` على `logic.py` (غيّروا سطر الاستيراد في أول الملف إلى `from logic import PlanBoard, EXPIRY_GRACE_SECONDS`). لو نجحت كلها يشتغل التبديل بدون ما نغيّر شيء في الواجهة.

**ملاحظة:** الاختبارات تستخدم `demo_fast_forward(minutes)`، وهي دالة تحرّك `created_at` لكل الخطط للخلف بعدد الدقائق (لتجربة المراحل بدون انتظار). أضيفوها في `PlanBoard` للاختبار فقط، والواجهة ما تستدعيها.

## 5) خطوة الدمج (عند فريق الواجهة)

افتح `ui/contract.py` وغيّر اسم الوحدة في سطر الاستيراد من `ui.dummy_logic` إلى `logic`. ثم احذف `ui/dummy_logic.py`.
