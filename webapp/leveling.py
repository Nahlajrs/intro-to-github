"""تحديد المستوى الوظيفي (Tier) واستخراج اسم المجال من المسمى الوظيفي — القسم 3 من المواصفة."""
import re

# الترتيب مهم: العبارات الأكثر تحديدًا أولًا (مثال: "مدير تنفيذي" قبل "مدير").
TIER_RULES = [
    (1, ["الرئيس التنفيذي", "الرئيس العام", "نائب الرئيس"], "قطاع", "tier_1", "نائب الرئيس"),
    (2, ["مدير تنفيذي", "مدير أول", "مدير إدارة"], "إدارة", "tier_2", "مدير تنفيذي / مدير أول"),
    (3, ["مدير عام", "مدير"], "قسم", "tier_3", "مدير عام / مدير"),
    (4, ["قائد فريق", "مدير مساعد", "رئيس قسم", "مشرف"], "فريق", "tier_4", "قائد فريق / مدير مساعد"),
    (5, ["أخصائي أول", "متخصص أول", "استشاري أول"], "فريق", "tier_5_6", "أخصائي أول / متخصص أول"),
    (6, ["أخصائي", "محلل", "مهندس", "مستشار"], "فريق", "tier_5_6", "أخصائي / محلل / مهندس"),
    (7, ["أخصائي مساعد", "فني", "موظف"], "فريق", "tier_7", "أخصائي مساعد / فني / موظف"),
]

EXPERIENCE_TABLE = {
    1: {"experience_years": "١٥+ سنة", "supervisory_years": "٨+ سنوات"},
    2: {"experience_years": "١٢ سنة", "supervisory_years": "٦ سنوات"},
    3: {"experience_years": "٨-١٠ سنوات", "supervisory_years": "٣-٤ سنوات"},
    4: {"experience_years": "٦-٨ سنوات", "supervisory_years": "٢-٣ سنوات"},
    5: {"experience_years": "٥-٧ سنوات", "supervisory_years": None},
    6: {"experience_years": "٣-٥ سنوات", "supervisory_years": None},
    7: {"experience_years": "١-٣ سنوات", "supervisory_years": None},
}

_SEPARATORS = re.compile(r"^[\s\-–:]+")


def normalize_title(raw: str) -> str:
    """توحيد المسمى للمطابقة في الأرشيف: إزالة التشكيل، توحيد الفواصل، وضغط المسافات."""
    text = raw.strip()
    text = re.sub(r"[ً-ْٰ]", "", text)  # إزالة التشكيل
    text = re.sub(r"[–—]", "-", text)  # توحيد الشرطات
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def detect_tier(job_title: str):
    """أرجع (tier, org_unit_noun, template_ref, level_label, matched_keyword)."""
    title = job_title.strip()
    for tier, keywords, org_unit_noun, template_ref, level_label in TIER_RULES:
        for kw in keywords:
            if kw in title:
                return tier, org_unit_noun, template_ref, level_label, kw
    # لم تتضح كلمة المستوى: أقرب تقدير منطقي (المستوى 5 كافتراضي متحفظ لمساهم فردي أول)
    return 5, "فريق", "tier_5_6", "أخصائي أول / متخصص أول", None


def extract_domain(job_title: str, matched_keyword: str) -> str:
    """احذف كلمة المستوى من بداية المسمى وأرجع اسم المجال المتبقي."""
    title = job_title.strip()
    if not matched_keyword:
        return title
    idx = title.find(matched_keyword)
    if idx != 0:
        # المسمى لا يبدأ بكلمة المستوى بوضوح: استخدم المسمى كاملاً
        return title
    remainder = title[idx + len(matched_keyword):]
    remainder = _SEPARATORS.sub("", remainder).strip()
    return remainder if remainder else title


def analyze(job_title: str) -> dict:
    tier, org_unit_noun, template_ref, level_label, matched_keyword = detect_tier(job_title)
    domain_name = extract_domain(job_title, matched_keyword)
    experience = EXPERIENCE_TABLE[tier]
    return {
        "job_title": job_title,
        "level_tier": tier,
        "level_label": level_label,
        "org_unit_noun": org_unit_noun,
        "domain_name": domain_name,
        "core_responsibilities_template_ref": template_ref,
        "experience_years": experience["experience_years"],
        "supervisory_years": experience["supervisory_years"],
    }
