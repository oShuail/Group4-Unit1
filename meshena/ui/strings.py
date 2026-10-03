"""strings.py - every user-facing string (Arabic) in one place, plus small text helpers."""

# Arabic text for each message the logic can return (the logic always returns English).
MSG = {
    "Enter your name first": "اكتب اسمك أولًا",
    "Title is required": "العنوان مطلوب",
    "Place is required": "المكان مطلوب",
    "Start must be between 1 and 60 minutes": "وقت الانتظار لازم يكون بين ١ و ٦٠ دقيقة",
    "Duration must be between 5 and 240 minutes": "مدة الخطة لازم تكون بين ٥ و ٢٤٠ دقيقة",
    "Plan posted": "تم نشر خطتك",
    "You joined": "تم انضمامك!",
    "You already joined": "أنت منضم من قبل",
    "Plan not found or expired": "الخطة غير موجودة أو انتهت",
    "You left the plan": "غادرت الخطة",
    "The host cannot leave, cancel instead": "صاحب الخطة ما يقدر يغادر، الغِ الخطة بدلًا من ذلك",
    "You are not in this plan": "أنت مو منضم لهذي الخطة",
    "Plan cancelled": "تم إلغاء الخطة",
    "Only the host can cancel": "بس صاحب الخطة يقدر يلغيها",
    "Name updated": "تم تغيير الاسم",
    "Plan is full": "اكتملت الخطة",
    "Capacity must be between 2 and 50": "عدد المنضمين لازم يكون بين ٢ و ٥٠",
}

# Arabic category names (the logic uses the English names).
CAT_AR = {"Lunch": "غداء", "Study": "دراسة", "Work": "عمل",
          "Discussion": "نقاش", "Tuwaiq Talk": "حديث طويق", "Other": "أخرى"}
CAT_EN = {arabic: english for english, arabic in CAT_AR.items()}  # for searching in Arabic

T = {
    "page_title": "مشينا | Join Me",
    # name page
    "welcome": "يا هلا فيك! خطوة بسيطة ونبدأ... وش نناديك؟",
    "name_hint": "مثلاً: رند",
    "name_btn": "يلا مشينا",
    "name_empty": "اكتب اسمك أولًا عشان نكمل.",
    # top bar and feed
    "search": "بحث عن خطة",
    "post": "انشر خطة",
    "leave_first": "غادر خطتك الحالية أولًا",
    "no_plans": "ما فيه خطط الحين، انشر أول خطة",
    "no_match": "ما لقينا خطط تطابق بحثك",
    "my_plan_host": "أنت منظم هذي الخطة",
    "my_plan_joined": "أنت منضم إلى",
    "view_plan": "عرض الخطة",
    "starts_in": "يبدأ بعد {n} دقيقة",
    "started": "بدأت الآن",
    "running": "جارية الآن",
    "joined_count": "{n} من {cap} منضم",
    "hosted_by": "بواسطة {name}",
    "join": "انضم",
    "leave": "غادر",
    "cancel": "إلغاء الخطة",
    "join_closed": "انتهى وقت الانضمام",
    "in_plan_notice": "أنت في خطة، غادرها لتنضم لغيرها",
    "full": "اكتملت الخطة",
    "all": "الكل",
    "empty_hint": "ابدأ أول خطة وخلّ غيرك ينضم لك",
    # plan pages
    "back": "رجوع",
    "leave_plan": "مغادرة الخطة",
    "participants": "المنضمون",
    "host_tag": "صاحب الخطة",
    "you": "أنت",
    "wait_left": "ينتهي الانتظار بعد",
    "plan_left": "تنتهي الخطة بعد",
    "hero_host_wait": "خطتك قيد الإنشاء",
    "hero_host_wait_sub": "وقت الانتظار ما انتهى، تقدر تتابع المنضمين هنا",
    "hero_host_run": "بدأت خطتك!",
    "hero_host_run_sub": "الكل في مكانه، استمتعوا بوقتكم",
    "hero_join_wait": "تم انضمامك!",
    "hero_join_wait_sub": "مقعدك محجوز، لا تتأخر علينا",
    "hero_join_run": "بدأت الخطة!",
    "hero_join_run_sub": "الحق عليهم في المكان",
    "plan_ended": "انتهت الخطة",
    "plan_gone": "الخطة انتهت أو تم إلغاؤها",
    # dialogs
    "dlg_post": "انشر خطة",
    "f_title": "العنوان",
    "f_category": "التصنيف",
    "f_place": "المكان",
    "f_description": "الوصف (اختياري)",
    "f_wait": "يبدأ بعد",
    "f_duration": "مدة الخطة",
    "f_capacity": "الحد الأقصى للمنضمين",
    "f_name": "تنشر باسم",
    "f_name_hint": "تقدر تغيّر الاسم من الشريط العلوي",
    "f_post": "انشر الخطة",
    "minutes": "{n} دقيقة",
    "dlg_rename": "تغيير الاسم",
    "f_new_name": "اسمك الجديد",
    "save": "حفظ",
    "dlg_leave": "تأكيد المغادرة",
    "dlg_leave_q": "متأكد إنك تبي تغادر الخطة؟",
    "stay": "ابقَ",
    "dlg_cancel": "تأكيد إلغاء الخطة",
    "dlg_cancel_q": "متأكد إنك تبي تلغي الخطة؟",
    "go_back": "ارجع",
}

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def ar(value):
    """Write a number with Arabic-Indic digits."""
    return str(value).translate(AR_DIGITS)


def fmt_clock(seconds):
    """Seconds as mm:ss (or h:mm:ss), with Arabic digits."""
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    text = f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"
    return ar(text)


def fmt_duration(minutes):
    """A plan length in words: 15 -> '١٥ دقيقة', 60 -> 'ساعة', 120 -> 'ساعتان'."""
    if minutes < 60:
        return T["minutes"].format(n=ar(minutes))
    hours, rest = divmod(minutes, 60)
    words = {1: "ساعة", 2: "ساعتان"}.get(hours, f"{ar(hours)} ساعات")
    if rest == 30:
        return f"{words} ونصف"
    if rest:
        return f"{words} و{T['minutes'].format(n=ar(rest))}"
    return words
