"""خط الإنتاج الكامل لبطاقة الوصف الوظيفي — يجمع القسم 3 (ثابت) مع الأقسام المولَّدة."""
from content_generator import generate_variable_sections
from core_templates import render_core_responsibilities
from leveling import analyze, split_sub_units


def build_content(job_title: str, sub_units_raw: str = "") -> dict:
    info = analyze(job_title)
    sub_units = split_sub_units(sub_units_raw)
    variable = generate_variable_sections(info, sub_units)
    # القسم 3 (الأساسي) يعتمد فقط على المستوى والمجال المستخرج من المسمى — لا علاقة له
    # بالإدارات/الأقسام التابعة، تمامًا كما في القالب الثابت المعتمد.
    core = render_core_responsibilities(info["core_responsibilities_template_ref"], info["domain_name"])

    qualifications = dict(variable["qualifications"])
    qualifications["experience_years"] = info["experience_years"]
    if info["supervisory_years"]:
        qualifications["supervisory_years"] = info["supervisory_years"]

    return {
        "job_title": info["job_title"],
        "level_tier": info["level_tier"],
        "level_label": info["level_label"],
        "org_unit_noun": info["org_unit_noun"],
        "domain_name": info["domain_name"],
        "sub_units_raw": sub_units_raw.strip(),
        "basic_info": {
            "job_code": "",
            "direct_manager": "",
            "sector": "",
            "department": "",
            "section": "",
        },
        "job_purpose": variable["job_purpose"],
        "core_responsibilities_template_ref": info["core_responsibilities_template_ref"],
        "core_responsibilities": core,
        "specialized_responsibilities": variable["specialized_responsibilities"],
        "qualifications": qualifications,
        "technical_competencies": variable.get("technical_competencies", []),
        "generation_source": variable.get("generation_source", "llm"),
        "generation_error": variable.get("generation_error"),
    }
