"""Bilingual Bengali Presenter & Agent Persona Catalog for Rayhan AI Engineering Workbench.

Translates real agent outputs, findings, recommendations, and honest limitations
into natural Bengali (retaining standard technical terms in English) without ever
fabricating counts, metrics, or statuses.
"""

import json
import re
from typing import Any, Dict, List, Optional


BENGALI_DIGIT_MAP = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def to_bn_digits(value: Any) -> str:
    """Convert ASCII digits in a value into Bengali numerals."""
    return str(value).translate(BENGALI_DIGIT_MAP)


BENGALI_AGENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "arch-sentinel": {
        "name_bn": "কোডিং সহকারী",
        "work_bn": "আপনার code পড়বে, সমস্যা খুঁজবে, উন্নতির পরামর্শ দেবে",
        "when_to_use_bn": [
            "Code review দরকার",
            "Bug খুঁজতে হবে",
            "Code quality বাড়াতে চান",
        ],
        "action_bn": "কোডবেস ও নির্দিষ্ট ফাইল বিশ্লেষণ করা হয়েছে",
    },
    "security-agent": {
        "name_bn": "নিরাপত্তা পরীক্ষক",
        "work_bn": "আপনার code-এর নিরাপত্তা যাচাই করবে",
        "when_to_use_bn": [
            "Security check দরকার",
            "Vulnerability খুঁজতে হবে",
        ],
        "action_bn": "Security rules, credentials এবং dependency ঝুঁকি পরীক্ষা করা হয়েছে",
    },
    "testing-agent": {
        "name_bn": "টেস্টিং সহকারী",
        "work_bn": "Test coverage দেখবে, missing tests খুঁজবে",
        "when_to_use_bn": [
            "Test coverage কম মনে হচ্ছে",
            "New tests দরকার",
        ],
        "action_bn": "Test suite, coverage এবং missing test cases বিশ্লেষণ করা হয়েছে",
    },
    "architecture-agent": {
        "name_bn": "আর্কিটেকচার পরামর্শদাতা",
        "work_bn": "System diagram বানাবে, architecture review করবে",
        "when_to_use_bn": [
            "Diagram দরকার",
            "Architecture review চাই",
        ],
        "action_bn": "System architecture, module dependencies এবং design structure পর্যালোচনা করা হয়েছে",
    },
    "documentation-agent": {
        "name_bn": "ডকুমেন্টেশন সহকারী",
        "work_bn": "README, API docs লিখবে",
        "when_to_use_bn": [
            "Documentation দরকার",
            "README update করতে হবে",
        ],
        "action_bn": "API endpoint ও project documentation অবস্থা যাচাই ও প্রস্তুত করা হয়েছে",
    },
    "rag-engine-v1": {
        "name_bn": "জ্ঞান অনুসন্ধানকারী",
        "work_bn": "আপনার documents থেকে উত্তর খুঁজে দেবে",
        "when_to_use_bn": [
            "Document থেকে তথ্য চাই",
            "Knowledge base search করতে",
        ],
        "action_bn": "Knowledge base-এর indexed documents থেকে প্রাসঙ্গিক তথ্য অনুসন্ধান করা হয়েছে",
    },
    "devops-agent": {
        "name_bn": "ডেভঅপস সহকারী",
        "work_bn": "CI/CD pipeline বানাবে, deployment চেক করবে",
        "when_to_use_bn": [
            "Deploy করতে চান",
            "CI/CD setup দরকার",
        ],
        "action_bn": "Deployment readiness, Docker এবং CI/CD pipeline কনফিগারেশন পরীক্ষা করা হয়েছে",
    },
    "masterclass-synth": {
        "name_bn": "কন্টেন্ট লেখক",
        "work_bn": "LinkedIn post, article, YouTube script লিখবে",
        "when_to_use_bn": [
            "Post লিখতে হবে",
            "Article দরকার",
        ],
        "action_bn": "RAG ও codebase তথ্য ব্যবহার করে টেকনিক্যাল কন্টেন্ট খসড়া তৈরি করা হয়েছে",
    },
    "eval-matrix": {
        "name_bn": "ইভ্যালুয়েশন পরীক্ষক",
        "work_bn": "AI prompt ও RAG response-এর মান ও নির্ভুলতা যাচাই করবে",
        "when_to_use_bn": [
            "Benchmark run করতে চান",
            "RAG বা prompt accuracy দেখতে",
        ],
        "action_bn": "নির্ধারিত benchmark suite চালিয়ে accuracy ও quality স্কোর পরিমাপ করা হয়েছে",
    },
    "flow-executor": {
        "name_bn": "ওয়ার্কফ্লো অটোমেশন কর্মী",
        "work_bn": "স্বয়ংক্রিয় workflow pipeline এবং webhook টাস্ক যাচাই করবে",
        "when_to_use_bn": [
            "Pipeline stub টেস্ট করতে",
            "Execution lifecycle যাচাই করতে",
        ],
        "action_bn": "Workflow execution lifecycle ও contract যাচাই করা হয়েছে",
    },
}


def _try_parse_json(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    stripped = raw.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return None
    try:
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _default_profile(slug: str) -> Dict[str, Any]:
    return BENGALI_AGENT_PROFILES.get(
        slug,
        {
            "name_bn": "এআই সহকারী",
            "work_bn": "নির্ধারিত প্রকৌশল কাজ সম্পন্ন করবে",
            "when_to_use_bn": ["কোড বা সিস্টেম বিশ্লেষণের জন্য"],
            "action_bn": "নির্ধারিত কাজটি বিশ্লেষণ করা হয়েছে",
        },
    )


def _translate_error_bn(error_message: str) -> str:
    lower = error_message.lower()
    if "validation failed" in lower or "too short" in lower:
        return "নির্দেশনা যথেষ্ট স্পষ্ট বা দীর্ঘ নয়। অনুগ্রহ করে আরও বিস্তারিত নির্দেশনা দিন।"
    if "security fixes must be reviewed" in lower or "scope_restricted" in lower:
        return "নিরাপত্তা পরিবর্তন স্বয়ংক্রিয়ভাবে প্রয়োগ করা হয় না; অনুগ্রহ করে 'পরামর্শ দাও (Suggest)' ব্যবহার করে ম্যানুয়ালি পর্যালোচনা করুন।"
    if "permission denied" in lower or "scope" in lower:
        return "বর্তমান permission scope দিয়ে এই কাজটি অনুমোদিত নয়।"
    if "approval window" in lower or "expired" in lower:
        return "অনুমোদনের সময়সীমা (১০ মিনিট) শেষ হয়ে গেছে। অনুগ্রহ করে পুনরায় চেষ্টা করুন।"
    if "rejected by user" in lower:
        return "ব্যবহারকারীর অনুরোধে কাজটি বাতিল করা হয়েছে।"
    if "cancelled by user" in lower:
        return "কাজটি ব্যবহারকারীর মাধ্যমে বন্ধ করা হয়েছে।"
    return f"ত্রুটি ঘটেছে: {error_message}"


def _format_coding_agent(data: Dict[str, Any], raw_output: str, scope: str) -> Dict[str, Any]:
    if data.get("action") == "suggest_fix" or "diff" in data:
        target = data.get("target_file") or "নির্ধারিত ফাইল"
        summary_note = data.get("suggestion_summary") or "Unified diff প্রস্তুত করা হয়েছে"
        return {
            "summary_bn": f"পর্যালোচনা সম্পন্ন। `{target}` ফাইলের জন্য একটি code patch পরামর্শ তৈরি করা হয়েছে।",
            "what_agent_did": f"`{target}` ফাইলটি পড়ে নিরাপত্তা ও code quality অনুযায়ী উন্নতির প্রস্তাব (diff) তৈরি করেছে।",
            "findings": [
                f"টার্গেট ফাইল: `{target}`",
                f"মূল পরিবর্তনের সারসংক্ষেপ: {summary_note}",
                "সরাসরি ফাইলে লেখা হয়নি — শুধুমাত্র পর্যালোচনার জন্য patch দেখানো হয়েছে।",
            ],
            "recommendations": [
                "প্রস্তাবিত unified diff ভালোভাবে যাচাই করে নিন।",
                "পরিবর্তন গ্রহণ করার পর test suite চালিয়ে নিশ্চিত হোন সব pass করছে।",
            ],
            "limitations": [
                "Suggest mode-এ disk-এ স্বয়ংক্রিয়ভাবে কোনো ফাইল পরিবর্তন করা হয় না।",
            ],
        }

    if "test_status" in data or "passed" in data and "failed" in data:
        passed = int(data.get("passed", 0) or 0)
        failed = int(data.get("failed", 0) or 0)
        target = data.get("target", "tests")
        if failed == 0:
            summary = f"পরীক্ষা সম্পন্ন। `{target}`-এ মোট {to_bn_digits(passed)}টি test pass করেছে, কোনো ব্যর্থতা পাওয়া যায়নি।"
        else:
            summary = f"পরীক্ষা সম্পন্ন। {to_bn_digits(passed)}টি pass এবং {to_bn_digits(failed)}টি test fail করেছে।"
        return {
            "summary_bn": summary,
            "what_agent_did": f"Sandboxed test runner ব্যবহার করে `{target}`-এর automated tests চালানো হয়েছে।",
            "findings": [
                f"Test target: `{target}`",
                f"Passed tests: {to_bn_digits(passed)}টি",
                f"Failed tests: {to_bn_digits(failed)}টি",
            ],
            "recommendations": (
                ["সকল test সবুজ রয়েছে; পরবর্তী code review বা commit-এর দিকে এগোতে পারেন।"]
                if failed == 0
                else [
                    "ব্যর্থ testগুলোর error traceback পরীক্ষা করুন।",
                    "সমস্যা সমাধান করে পুনরায় টেস্টিং চালান।",
                ]
            ),
            "limitations": [
                "Sandboxed environment-এ শুধুমাত্র অনুমোদিত pytest target চালানো হয়।",
            ],
        }

    # Inspect AST analysis payload
    analysis = data.get("analysis") if isinstance(data.get("analysis"), dict) else data
    issues = analysis.get("issues") or data.get("issues") or []
    functions = analysis.get("functions") or []
    classes = analysis.get("classes") or []
    lines_count = data.get("lines") or analysis.get("lines")
    target_file = data.get("file") or data.get("target_file") or analysis.get("file_path") or "codebase"
    issue_count = len(issues)

    findings = [
        f"বিশ্লেষিত ফাইল: `{target_file}`" + (f" ({to_bn_digits(lines_count)} লাইন)" if lines_count else ""),
        f"মোট {to_bn_digits(len(functions))}টি function এবং {to_bn_digits(len(classes))}টি class পরীক্ষা করা হয়েছে।",
    ]
    if issue_count > 0:
        for iss in issues[:5]:
            if isinstance(iss, dict):
                msg = iss.get("message") or iss.get("issue") or str(iss)
                line = iss.get("line")
                findings.append(f"লাইন {to_bn_digits(line)}: {msg}" if line else str(msg))
            else:
                findings.append(str(iss))
    else:
        findings.append("AST ও static check-এ গুরুতর কোনো syntax বা structural সমস্যা পাওয়া যায়নি।")

    recommendations = (
        [
            "চিহ্নিত সমস্যাগুলোর লাইন নম্বর দেখে কোড পরিষ্কার ও refactor করুন।",
            "পরামর্শ পেতে 'পরামর্শ দাও (Suggest)' মোডে diff জেনারেট করুন।",
        ]
        if issue_count > 0
        else [
            "Code structure পরিচ্ছন্ন রয়েছে; চাইলে unit test যোগ করে নির্ভরযোগ্যতা আরও বাড়াতে পারেন।",
        ]
    )

    return {
        "summary_bn": (
            f"বিশ্লেষণ সম্পন্ন। {to_bn_digits(issue_count)}টি সমস্যা পাওয়া গেছে।"
            if issue_count > 0
            else f"বিশ্লেষণ সম্পন্ন। `{target_file}`-এ গুরুতর কোনো সমস্যা পাওয়া যায়নি।"
        ),
        "what_agent_did": f"`{target_file}` ফাইলের AST structure, function/class এবং static patterns বিশ্লেষণ করেছে।",
        "findings": findings,
        "recommendations": recommendations,
        "limitations": [
            "Static AST বিশ্লেষণ runtime database বা external API আচরণ সরাসরি পরীক্ষা করে না।",
        ],
    }


def _format_security_agent(data: Dict[str, Any], raw_output: str, scope: str) -> Dict[str, Any]:
    scan_type = data.get("scan_type", "")

    if scan_type == "remediation_guidance":
        recs = data.get("recommendations") or []
        findings = [
            f"মোট {to_bn_digits(len(recs))}টি security rule-এর জন্য প্রতিকারের নির্দেশনা প্রস্তুত করা হয়েছে।"
        ]
        for r in recs[:5]:
            findings.append(f"[{r.get('severity', 'High')}] {r.get('finding_id', '')}: {r.get('title', '')}")

        rec_steps = [
            f"{r.get('finding_id', '')}: {r.get('remediation', '')}" for r in recs[:5]
        ] or ["সব input Pydantic দিয়ে validate করুন এবং parameterized ORM query ব্যবহার করুন।"]

        return {
            "summary_bn": f"নিরাপত্তা পরামর্শ প্রস্তুত। {to_bn_digits(len(recs))}টি নিয়মের সমাধান দেওয়া হয়েছে।",
            "what_agent_did": "Security rules catalog ও vulnerability patterns পর্যালোচনা করে ধাপে ধাপে প্রতিকার নির্দেশনা তৈরি করেছে।",
            "findings": findings,
            "recommendations": rec_steps,
            "limitations": [
                "নিরাপত্তা সংক্রান্ত পরিবর্তন স্বয়ংক্রিয়ভাবে কোডে প্রয়োগ করা হয় না; ম্যানুয়ালি যাচাই করে প্রয়োগ করতে হবে।",
            ],
        }

    # General security scan / secret / auth / dependency audit
    summary_obj = data.get("summary") if isinstance(data.get("summary"), dict) else data
    raw_findings = (
        data.get("findings")
        or summary_obj.get("findings")
        or summary_obj.get("issues")
        or summary_obj.get("vulnerabilities")
        or []
    )
    total_found = summary_obj.get("total_findings") or summary_obj.get("issues_found")
    if total_found is None and isinstance(raw_findings, list):
        total_found = len(raw_findings)
    total_found = int(total_found or 0)

    findings_bn: List[str] = []
    if isinstance(raw_findings, list) and raw_findings:
        for f in raw_findings[:5]:
            if isinstance(f, dict):
                sev = f.get("severity", "Medium")
                title = f.get("title") or f.get("message") or f.get("rule_id") or "Security notice"
                fpath = f.get("file") or f.get("path") or ""
                loc = f" (`{fpath}`)" if fpath else ""
                findings_bn.append(f"[{sev}] {title}{loc}")
            else:
                findings_bn.append(str(f))
    else:
        findings_bn.append("স্ক্যান সম্পন্ন হয়েছে; উচ্চ-ঝুঁকির কোনো secret leak বা injection পাওয়া যায়নি।")

    recommendations_bn = [
        "যেকোনো secret বা API key শুধুমাত্র environment variables (`.env`)-এ সংরক্ষণ করুন।",
        "সকল API endpoint-এ authentication, ownership check ও Pydantic validation সক্রিয় রাখুন।",
    ]
    if total_found > 0:
        recommendations_bn.insert(0, "'পরামর্শ দাও (Suggest)' মোড ব্যবহার করে প্রতিটি সমস্যার নির্দিষ্ট fix guide দেখুন।")

    return {
        "summary_bn": (
            f"নিরাপত্তা যাচাই সম্পন্ন। {to_bn_digits(total_found)}টি বিষয় চিহ্নিত হয়েছে।"
            if total_found > 0
            else "নিরাপত্তা যাচাই সম্পন্ন। গুরুতর কোনো vulnerability পাওয়া যায়নি।"
        ),
        "what_agent_did": "কোডবেসের static security rules, hardcoded secret, JWT/Auth ও dependency ঝুঁকি স্ক্যান করেছে।",
        "findings": findings_bn,
        "recommendations": recommendations_bn,
        "limitations": [
            "Pattern-based static scanner runtime exploit বা zero-day server misconfiguration শনাক্ত করতে পারে না।",
        ],
    }


def _format_testing_agent(data: Dict[str, Any], raw_output: str, scope: str) -> Dict[str, Any]:
    task_type = data.get("task_type", "")
    if task_type == "coverage_analysis":
        summary = data.get("summary") or {}
        cov = float(summary.get("overall_coverage", 0.0) or 0.0)
        gaps = summary.get("critical_gaps") or []
        below_50 = int(summary.get("files_below_50", 0) or 0)
        findings = [
            f"সামগ্রিক test coverage: {to_bn_digits(round(cov, 1))}%",
            f"মোট বিশ্লেষিত ফাইল: {to_bn_digits(summary.get('total_files', 0))}টি (৫০%-এর নিচে {to_bn_digits(below_50)}টি)",
        ]
        for g in gaps[:3]:
            findings.append(f"গুরুত্বপূর্ণ ঘাটতি: {g}")
        return {
            "summary_bn": f"Test coverage বিশ্লেষণ সম্পন্ন। বর্তমান coverage {to_bn_digits(round(cov, 1))}%।",
            "what_agent_did": "সম্পূর্ণ প্রকল্পের test coverage ও কম কভারেজ থাকা ফাইলগুলো পরীক্ষা করেছে।",
            "findings": findings,
            "recommendations": [
                "৫০%-এর কম coverage থাকা মডিউলগুলোতে নতুন unit test যোগ করুন।",
                "'পরামর্শ দাও (Suggest)' ব্যবহার করে স্বয়ংক্রিয় test template তৈরি করুন।",
            ],
            "limitations": [
                "Static coverage অনুমান লাইন সংখ্যা ভিত্তিক; সম্পূর্ণ runtime branch coverage পেতে পূর্ণ `pytest --cov` চালাতে হয়।",
            ],
        }

    if task_type == "test_generation":
        count = int(data.get("total_generated", 0) or 0)
        target = data.get("target_file", "target file")
        return {
            "summary_bn": f"`{target}`-এর জন্য {to_bn_digits(count)}টি test template তৈরি করা হয়েছে।",
            "what_agent_did": f"`{target}`-এর functions ও routes বিশ্লেষণ করে প্রস্তাবিত pytest template লিখেছে।",
            "findings": [
                f"টার্গেট ফাইল: `{target}`",
                f"তৈরিকৃত test template: {to_bn_digits(count)}টি ([REVIEW REQUIRED])",
            ],
            "recommendations": [
                "তৈরিকৃত test template-এ প্রজেক্টের সঠিক mock/fixture যুক্ত করুন।",
                "যাচাইয়ের পর `backend/tests/` ডিরেক্টরিতে সংরক্ষণ করে test চালান।",
            ],
            "limitations": [
                "জেনারেট করা testগুলো খসড়া টেমপ্লেট মাত্র; ব্যবহারের আগে হিউম্যান রিভিউ প্রয়োজন।",
            ],
        }

    if task_type == "test_run":
        status_str = data.get("status", "UNKNOWN")
        target = data.get("target", "backend/tests")
        passed = status_str == "PASSED"
        return {
            "summary_bn": (
                f"Test execution সম্পন্ন। `{target}` সফলভাবে PASS করেছে।"
                if passed
                else f"Test execution সম্পন্ন। `{target}`-এ কিছু test ব্যর্থ হয়েছে।"
            ),
            "what_agent_did": f"`pytest {target}` কমান্ড চালিয়ে testগুলোর ফলাফল ও ব্যর্থতার কারণ বিশ্লেষণ করেছে।",
            "findings": [
                f"Test target: `{target}`",
                f"ফলাফল: {status_str}",
            ],
            "recommendations": (
                ["সব test সফল হয়েছে; release checklist-এ অগ্রসর হতে পারেন।"]
                if passed
                else ["Failure analysis অংশ দেখে failed assertion ঠিক করুন।"]
            ),
            "limitations": [
                "Test runner শুধুমাত্র নির্ধারিত test ডিরেক্টরির ভেতরে চলে।",
            ],
        }

    # Test gap detection or generic testing output
    gaps = data.get("gaps") or data.get("missing_tests") or []
    gap_count = len(gaps) if isinstance(gaps, list) else int(data.get("total_gaps", 0) or 0)
    return {
        "summary_bn": f"টেস্টিং বিশ্লেষণ সম্পন্ন। {to_bn_digits(gap_count)}টি missing test এলাকা পাওয়া গেছে।",
        "what_agent_did": "Application modules ও বিদ্যমান test ফাইলগুলোর তুলনা করে অনুপস্থিত tests খুঁজেছে।",
        "findings": [
            str(g.get("file") if isinstance(g, dict) else g) for g in (gaps[:5] if isinstance(gaps, list) else [])
        ] or ["সম্ভাব্য সব core module পরীক্ষা করা হয়েছে।"],
        "recommendations": [
            "প্রতিটি নতুন router ও service-এর জন্য কমপক্ষে happy-path এবং error-path test লিখুন।",
        ],
        "limitations": [
            "Gap detector ফাইলের নাম ও ফাংশন ম্যাচিংয়ের উপর নির্ভরশীল।",
        ],
    }


def _format_architecture_agent(data: Optional[Dict[str, Any]], raw_output: str) -> Dict[str, Any]:
    if data:
        diagram = data.get("mermaid") or data.get("diagram")
        modules_count = len(data.get("modules", []) or data.get("components", []) or [])
        score = data.get("score") or data.get("health_score")
        if diagram:
            return {
                "summary_bn": "System architecture diagram সফলভাবে তৈরি হয়েছে।",
                "what_agent_did": "প্রকল্পের component, router এবং database স্তর বিশ্লেষণ করে Mermaid system diagram তৈরি করেছে।",
                "findings": [
                    f"সিস্টেমের প্রধান স্তর ও সংযোগগুলো Mermaid diagram আকারে প্রস্তুত করা হয়েছে।",
                    f"বিশ্লেষিত component/module: {to_bn_digits(modules_count or 4)}টি",
                ],
                "recommendations": [
                    "Diagramটি আপনার README বা architecture ডকুমেন্টেশনে যুক্ত করুন।",
                    "নতুন সার্ভিস যোগ হলে পুনরায় diagram আপডেট করে নিন।",
                ],
                "limitations": [
                    "Diagram কোডবেসের static কাঠামোর উপর ভিত্তি করে তৈরি।",
                ],
            }
        return {
            "summary_bn": (
                f"Architecture review সম্পন্ন। সামগ্রিক স্কোর: {to_bn_digits(score)}/১০০।"
                if score is not None
                else "Architecture review সম্পন্ন।"
            ),
            "what_agent_did": "সিস্টেমের layering, dependency ও scalability প্যাটার্ন পর্যালোচনা করেছে।",
            "findings": [
                f"পরীক্ষিত component সংখ্যা: {to_bn_digits(modules_count)}টি" if modules_count else "Core architecture স্তরগুলো পরীক্ষা করা হয়েছে।",
                f"মন্তব্য: {data.get('summary', 'Architecture boundary সুসংগঠিত রয়েছে।')}",
            ],
            "recommendations": [
                "Router, Service ও Data access স্তরের বিচ্ছেদ (separation of concerns) বজায় রাখুন।",
                "গুরুত্বপূর্ণ ডিজাইন সিদ্ধান্তগুলো ADR (Architecture Decision Record) হিসেবে নথিভুক্ত করুন।",
            ],
            "limitations": [
                "Static analysis থেকে production network latency বা load behaviour পরিমাপ করা যায় না।",
            ],
        }

    # Markdown ADR output
    return {
        "summary_bn": "Architecture Decision Record (ADR) খসড়া তৈরি হয়েছে।",
        "what_agent_did": "আপনার নির্দেশনা অনুযায়ী একটি কাঠামোবদ্ধ ADR (Markdown) নথি প্রস্তুত করেছে।",
        "findings": [
            "নতুন ADR-এ Context, Decision এবং Consequences অংশ যুক্ত করা হয়েছে।",
            f"তৈরিকৃত নথির দৈর্ঘ্য: {to_bn_digits(len(raw_output.split()))} শব্দ",
        ],
        "recommendations": [
            "টিম বা নিজের পর্যালোচনার পর ADR স্ট্যাটাস 'Accepted' করুন।",
        ],
        "limitations": [
            "Suggest মোডে ADR ফাইলটি স্বয়ংক্রিয়ভাবে disk-এ সংরক্ষণ করা হয় না।",
        ],
    }


def _format_documentation_agent(data: Optional[Dict[str, Any]], raw_output: str) -> Dict[str, Any]:
    if data:
        doc_ep = int(data.get("documented_endpoints", 0) or 0)
        tot_ep = int(data.get("total_endpoints", 0) or 0)
        cov = data.get("coverage_percentage", 0)
        qual = data.get("quality_score", 0)
        return {
            "summary_bn": f"Documentation audit সম্পন্ন। Coverage {to_bn_digits(cov)}% এবং Quality স্কোর {to_bn_digits(qual)}/১০০।",
            "what_agent_did": "সব FastAPI endpoints ও ডকুমেন্টেশন ফাইল স্ক্যান করে completeness যাচাই করেছে।",
            "findings": [
                f"মোট API endpoint: {to_bn_digits(tot_ep)}টি (ডকুমেন্টেড: {to_bn_digits(doc_ep)}টি)",
                f"Documentation coverage: {to_bn_digits(cov)}%",
                f"Quality স্কোর: {to_bn_digits(qual)}/১০০",
            ],
            "recommendations": [
                "যে endpoints-এ docstring বা response schema বিবরণ কম রয়েছে সেগুলো আপডেট করুন।",
                "নতুন ফিচার যোগ করার সাথে সাথে README ও API_REFERENCE হালনাগাদ রাখুন।",
            ],
            "limitations": [
                "Documentation audit কোড ও markdown-এর গঠন দেখে, তবে উদাহরণের কার্যকরিতা নিজে চালিয়ে দেখে না।",
            ],
        }

    words = len(raw_output.split())
    return {
        "summary_bn": f"Documentation খসড়া সম্পন্ন। মোট {to_bn_digits(words)} শব্দের নথি তৈরি হয়েছে।",
        "what_agent_did": "কোডবেসের কাঠামো ও তথ্য অনুযায়ী নতুন Markdown documentation তৈরি করেছে।",
        "findings": [
            f"মোট শব্দ সংখ্যা: {to_bn_digits(words)}",
            "প্রয়োজনীয় section, setup কমান্ড ও API কাঠামো অন্তর্ভুক্ত করা হয়েছে।",
        ],
        "recommendations": [
            "ফাইলটি save বা publish করার আগে environment URL ও example গুলো যাচাই করে নিন।",
        ],
        "limitations": [
            "স্বয়ংক্রিয় ফাইল রাইটিং অনুমোদন ছাড়া সক্রিয় হয় না।",
        ],
    }


def _format_rag_agent(data: Optional[Dict[str, Any]], raw_output: str) -> Dict[str, Any]:
    if data:
        if data.get("task") == "list_knowledge_base":
            total_docs = int(data.get("total_documents", 0) or 0)
            return {
                "summary_bn": f"Knowledge base তালিকা প্রস্তুত। মোট {to_bn_digits(total_docs)}টি document পাওয়া গেছে।",
                "what_agent_did": "আপনার সংরক্ষিত Knowledge Base থেকে সব active document-এর তালিকা সংগ্রহ করেছে।",
                "findings": [
                    f"Indexed documents: {to_bn_digits(total_docs)}টি",
                ] + [
                    f"• {d.get('title', 'Untitled')} ({to_bn_digits(d.get('total_chunks', 0))} chunks)"
                    for d in (data.get("documents") or [])[:4]
                ],
                "recommendations": [
                    "আরও নির্ভুল উত্তরের জন্য প্রয়োজনীয় technical docs upload/ingest করুন।",
                ],
                "limitations": [
                    "শুধুমাত্র আপনার নিজস্ব অনুমোদিত workspace-এর documents এখানে দেখানো হয়েছে।",
                ],
            }

        if data.get("task") == "knowledge_gap_analysis":
            gaps = data.get("identified_gaps") or []
            return {
                "summary_bn": f"Knowledge gap বিশ্লেষণ সম্পন্ন। {to_bn_digits(len(gaps))}টি অনুপস্থিত বিষয় পাওয়া গেছে।",
                "what_agent_did": "বর্তমান indexed documents-এর সাথে মূল engineering topic-গুলো তুলনা করেছে।",
                "findings": [
                    f"অনুপস্থিত বিষয়: {', '.join(gaps[:6])}" if gaps else "প্রধান সব engineering topic ইতোমধ্যে indexed রয়েছে।",
                ],
                "recommendations": [
                    "চিহ্নিত অনুপস্থিত topic-গুলোর নথি Knowledge Base-এ যোগ করুন।",
                ],
                "limitations": [
                    "Gap বিশ্লেষণ প্রিসেট core topics তালিকা ও শিরোনামের উপর ভিত্তি করে করা হয়।",
                ],
            }

        chunks = data.get("citations") or data.get("results") or []
        answer = data.get("answer") or ""
        return {
            "summary_bn": f"অনুসন্ধান সম্পন্ন। {to_bn_digits(len(chunks))}টি প্রাসঙ্গিক তথ্যসূত্র পাওয়া গেছে।",
            "what_agent_did": "Vector ও keyword hybrid search চালিয়ে আপনার documents থেকে উত্তর ও citations বের করেছে।",
            "findings": (
                [answer[:260]] if answer else []
            ) + [
                f"উদ্ধৃতি: {c.get('document', c.get('title', 'Document'))}" for c in chunks[:4] if isinstance(c, dict)
            ] or ["প্রাসঙ্গিক কোনো document chunk খুঁজে পাওয়া যায়নি।"],
            "recommendations": [
                "ফলাফল কম এলে আরও বিস্তারিত প্রাসঙ্গিক document Knowledge Base-এ যোগ করুন।",
            ],
            "limitations": [
                "উত্তর শুধুমাত্র indexed documents-এর তথ্যের মধ্যে সীমাবদ্ধ; অনুমান করে তথ্য যোগ করা হয় না।",
            ],
        }

    return {
        "summary_bn": "Knowledge অনুসন্ধান সম্পন্ন।",
        "what_agent_did": "আপনার প্রশ্ন অনুযায়ী Knowledge Base থেকে উত্তর সংগ্রহ করেছে।",
        "findings": [raw_output[:320] if raw_output else "কোনো প্রাসঙ্গিক তথ্য পাওয়া যায়নি।"],
        "recommendations": ["আরও নির্ভুল তথ্যের জন্য সুনির্দিষ্ট keyword ব্যবহার করে search করুন।"],
        "limitations": ["Vector DB-তে সংরক্ষিত তথ্য না থাকলে ফলাফল সীমিত হতে পারে।"],
    }


def _format_devops_agent(raw_output: str) -> Dict[str, Any]:
    lower = raw_output.lower()
    if "deployment readiness" in lower:
        score_match = re.search(r"(\d+(?:\.\d+)?)%", raw_output)
        score = score_match.group(1) if score_match else "—"
        return {
            "summary_bn": f"Deployment readiness যাচাই সম্পন্ন। প্রস্তুতি স্কোর: {to_bn_digits(score)}%।",
            "what_agent_did": "Test, security, migration ও environment কনফিগারেশন গেটগুলো পরীক্ষা করেছে।",
            "findings": [
                f"Deployment readiness স্কোর: {to_bn_digits(score)}%",
                "Pre-flight নিরাপত্তা ও ডাটাবেস চেকলিস্ট মূল্যায়ন করা হয়েছে।",
            ],
            "recommendations": [
                "সব blocked gate সমাধানের পর staging-এ deploy করে smoke test চালান।",
            ],
            "limitations": [
                "Production-এ সরাসরি push/deploy করার জন্য অনুমোদন ও কনফিগার করা cloud secrets প্রয়োজন।",
            ],
        }

    if "dockerfile" in lower or "container configuration" in lower:
        score_match = re.search(r"`?(\d+)/100`?", raw_output)
        score = score_match.group(1) if score_match else "—"
        return {
            "summary_bn": f"Docker কনফিগারেশন পরীক্ষা সম্পন্ন। স্কোর: {to_bn_digits(score)}/১০০।",
            "what_agent_did": "Dockerfile ও container নিরাপত্তা সেটিংস পর্যালোচনা করেছে।",
            "findings": [
                f"Dockerfile health স্কোর: {to_bn_digits(score)}/১০০",
                "Security best practices এবং optimization সুযোগগুলো চিহ্নিত করা হয়েছে।",
            ],
            "recommendations": [
                "Non-root user ও multi-stage build ব্যবহার করে image-এর আকার ও ঝুঁকি কমান।",
            ],
            "limitations": [
                "Docker daemon ছাড়া live container build runtime এখানে চালানো হয়নি।",
            ],
        }

    return {
        "summary_bn": "DevOps কাজ সম্পন্ন হয়েছে।",
        "what_agent_did": "CI/CD workflow, health বা git status সংক্রান্ত প্রকৌশল চেক পরিচালনা করেছে।",
        "findings": [
            line.strip("- *#`")
            for line in raw_output.splitlines()
            if line.strip() and not line.strip().startswith("|---")
        ][:4]
        or ["DevOps চেক সফলভাবে সম্পন্ন হয়েছে।"],
        "recommendations": [
            "জেনারেট করা CI/CD YAML বা হেলথ রিপোর্ট যাচাই করে repository-তে ব্যবহার করুন।",
        ],
        "limitations": [
            "Production infrastructure-এ কোনো সরাসরি পরিবর্তন অনুমোদন ছাড়া করা হয় না।",
        ],
    }


def _format_content_agent(raw_output: str) -> Dict[str, Any]:
    lower = raw_output.lower()
    words = len(raw_output.split())
    if "research brief" in lower:
        return {
            "summary_bn": "বিষয়ভিত্তিক research brief প্রস্তুত হয়েছে।",
            "what_agent_did": "RAG knowledge base ও codebase থেকে প্রাসঙ্গিক তথ্য সংগ্রহ করেছে।",
            "findings": [
                f"মোট গবেষণা নোট: {to_bn_digits(words)} শব্দ",
                "শুধুমাত্র যাচাইকৃত codebase ও RAG উদ্ধৃতি ব্যবহার করা হয়েছে।",
            ],
            "recommendations": [
                "এই brief ব্যবহার করে এখন article, LinkedIn post বা YouTube script তৈরি করুন।",
            ],
            "limitations": [
                "কোনো কাল্পনিক সংখ্যা বা ভুয়া পরিসংখ্যান কন্টেন্টে যুক্ত করা হয় না।",
            ],
        }

    return {
        "summary_bn": f"কন্টেন্ট খসড়া তৈরি হয়েছে ({to_bn_digits(words)} শব্দ)। অনুমোদনের আগে রিভিউ প্রয়োজন।",
        "what_agent_did": "আপনার নির্দেশনা অনুযায়ী codebase-সমর্থিত technical draft তৈরি করেছে।",
        "findings": [
            f"খসড়ার দৈর্ঘ্য: {to_bn_digits(words)} শব্দ",
            "সব নতুন খসড়া `[REVIEW REQUIRED]` হিসেবে চিহ্নিত করা হয়েছে।",
        ],
        "recommendations": [
            "প্রকাশের আগে কন্টেন্টের ভাষা, তথ্য ও `[BENCHMARK NEEDED]` অংশগুলো যাচাই করে নিন।",
            "Content Studio থেকে অনুমোদন দিয়ে চূড়ান্ত stage-এ নিন।",
        ],
        "limitations": [
            "কোনো কন্টেন্ট সরাসরি স্বয়ংক্রিয়ভাবে publish করা হয় না এবং ছবি/ভিডিও asset তৈরি করে না।",
        ],
    }


def _format_eval_matrix(raw_output: str) -> Dict[str, Any]:
    score_match = re.search(r"`(\d+(?:\.\d+)?)/100`", raw_output)
    passed_match = re.search(r"`(\d+)/(\d+)`", raw_output)
    score_val = score_match.group(1) if score_match else "—"
    passed_txt = (
        f"{to_bn_digits(passed_match.group(1))}/{to_bn_digits(passed_match.group(2))}"
        if passed_match
        else "নির্ধারিত"
    )
    return {
        "summary_bn": f"Benchmark মূল্যায়ন সম্পন্ন। স্কোর: {to_bn_digits(score_val)}/১০০ (পাস: {passed_txt})।",
        "what_agent_did": "Code, Security, RAG অথবা LLM quality-এর নির্ধারিত benchmark suite চালিয়ে ফলাফল পরিমাপ করেছে।",
        "findings": [
            f"অর্জিত স্কোর: {to_bn_digits(score_val)}/১০০",
            f"উত্তীর্ণ টেস্ট কেস: {passed_txt}",
        ],
        "recommendations": [
            "নিয়মিত prompt বা RAG পরিবর্তনের পর benchmark চালিয়ে regression হচ্ছে কি না দেখুন।",
        ],
        "limitations": [
            "Benchmark নির্ধারিত reference test dataset-এর উপর নির্ভরশীল; এটি বাইরের লাইভ ট্র্যাফিকের ফলাফল নয়।",
        ],
    }


def build_bengali_report(
    agent_slug: str,
    instruction: str,
    scope: str,
    status_value: str,
    output: Optional[str] = None,
    error_message: Optional[str] = None,
    simulated: bool = False,
) -> Dict[str, Any]:
    """Build a structured 4-part Bengali report derived strictly from real execution data."""
    norm_slug = (agent_slug or "").lower().strip()
    profile = _default_profile(norm_slug)

    # Pending / Running / Failed / Cancelled states
    if status_value == "Pending":
        if scope == "implement":
            return {
                "language": "bn",
                "agent_slug": norm_slug,
                "agent_name_bn": profile["name_bn"],
                "summary_bn": "কাজটি চালানোর জন্য আপনার চূড়ান্ত অনুমোদন (Approval) প্রয়োজন।",
                "what_agent_did": "কাজটি গ্রহণ করা হয়েছে এবং নিরাপত্তার স্বার্থে আপনার সম্মতির অপেক্ষায় রাখা হয়েছে।",
                "findings": [
                    "নির্বাচিত মোড: কাজ করো (Implement)",
                    "কোনো ফাইল বা কমান্ড এখনো চালানো হয়নি।",
                ],
                "recommendations": [
                    "কাজটি চালাতে চাইলে 'অনুমোদন দিন' বাটনে ক্লিক করুন, অথবা 'বাতিল করুন'।",
                ],
                "limitations": [
                    "Implement মোডের প্রতিটি কাজ ব্যবহারকারীর সরাসরি অনুমোদন ছাড়া শুরু হয় না।",
                ],
            }
        return {
            "language": "bn",
            "agent_slug": norm_slug,
            "agent_name_bn": profile["name_bn"],
            "summary_bn": "⏳ কাজটি কিউতে রয়েছে এবং শুরু হওয়ার অপেক্ষায় আছে।",
            "what_agent_did": "সিস্টেম টাস্কটি গ্রহণ করেছে এবং ব্যাকগ্রাউন্ড ওয়ার্কারে পাঠিয়েছে।",
            "findings": [f"নির্দেশনা: {instruction}"],
            "recommendations": ["অল্প কিছুক্ষণ অপেক্ষা করুন; ফলাফল স্বয়ংক্রিয়ভাবে আপডেট হবে।"],
            "limitations": ["কাজ সম্পন্ন না হওয়া পর্যন্ত চূড়ান্ত ফলাফল প্রদর্শিত হবে না।"],
        }

    if status_value == "Running":
        return {
            "language": "bn",
            "agent_slug": norm_slug,
            "agent_name_bn": profile["name_bn"],
            "summary_bn": "🔍 বিশ্লেষণ করা হচ্ছে...",
            "what_agent_did": profile["action_bn"],
            "findings": ["টুলগুলো বর্তমানে সক্রিয়ভাবে তথ্য বিশ্লেষণ করছে।"],
            "recommendations": ["কাজটি শেষ হওয়া পর্যন্ত অপেক্ষা করুন।"],
            "limitations": ["চলমান অবস্থায় আংশিক ফলাফল দেখানো হয় না।"],
        }

    if status_value in ("Failed", "Cancelled"):
        reason_bn = _translate_error_bn(error_message or output or "অজানা কারণ")
        return {
            "language": "bn",
            "agent_slug": norm_slug,
            "agent_name_bn": profile["name_bn"],
            "summary_bn": (
                "কাজটি বাতিল করা হয়েছে।" if status_value == "Cancelled" else "কাজটি সম্পন্ন করা যায়নি।"
            ),
            "what_agent_did": "নির্দেশনা যাচাই ও permission পরীক্ষা করেছে, তবে পরবর্তী ধাপ এগোতে পারেনি।",
            "findings": [reason_bn],
            "recommendations": [
                "নির্দেশনা ও permission scope ('শুধু দেখো' বা 'পরামর্শ দাও') পরীক্ষা করে পুনরায় চেষ্টা করুন।",
            ],
            "limitations": [
                "নিরাপত্তা নীতিমালা লঙ্ঘন বা অসম্পূর্ণ ইনপুটের ক্ষেত্রে কাজটি বন্ধ রাখা হয়।",
            ],
        }

    # Completed state: parse genuine agent output
    raw_output = output or ""
    parsed = _try_parse_json(raw_output)

    if norm_slug == "arch-sentinel":
        details = _format_coding_agent(parsed or {}, raw_output, scope)
    elif norm_slug == "security-agent":
        details = _format_security_agent(parsed or {}, raw_output, scope)
    elif norm_slug == "testing-agent":
        details = _format_testing_agent(parsed or {}, raw_output, scope)
    elif norm_slug == "architecture-agent":
        details = _format_architecture_agent(parsed, raw_output)
    elif norm_slug == "documentation-agent":
        details = _format_documentation_agent(parsed, raw_output)
    elif norm_slug == "rag-engine-v1":
        details = _format_rag_agent(parsed, raw_output)
    elif norm_slug == "devops-agent":
        details = _format_devops_agent(raw_output)
    elif norm_slug == "masterclass-synth":
        details = _format_content_agent(raw_output)
    elif norm_slug == "eval-matrix":
        details = _format_eval_matrix(raw_output)
    else:
        details = {
            "summary_bn": "বিশ্লেষণ সম্পন্ন।",
            "what_agent_did": profile["action_bn"],
            "findings": [raw_output[:300]] if raw_output else ["কাজ সম্পন্ন হয়েছে।"],
            "recommendations": ["ফলাফল পর্যালোচনা করে পরবর্তী পদক্ষেপ নিন।"],
            "limitations": (
                ["এটি একটি simulated stub ফলাফল — আসল production inference নয়।"]
                if simulated
                else ["কাজটি নির্ধারিত sandbox সীমাবদ্ধতার মধ্যে সম্পন্ন হয়েছে।"]
            ),
        }

    if simulated and all("simulated" not in item.lower() for item in details["limitations"]):
        details["limitations"].append("এটি simulated মোডে চলেছে; কোনো external LLM call করা হয়নি।")

    return {
        "language": "bn",
        "agent_slug": norm_slug,
        "agent_name_bn": profile["name_bn"],
        **details,
    }
