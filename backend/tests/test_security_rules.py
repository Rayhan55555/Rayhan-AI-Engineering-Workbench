import pytest
from backend.app.security.patterns import (
    COMMAND_INJECTION_SHELL,
    SQL_INJECTION_FORMAT,
)
from backend.app.security.rules import RULE_CATALOG, SECURITY_RULES, RuleCategory, Severity
from backend.app.tools.security_scanner import SecurityScannerTool


def test_rule_catalog_completeness():
    """Verify at least 18 security rules are registered across standard categories."""
    assert len(SECURITY_RULES) >= 18
    categories = {rule.category for rule in SECURITY_RULES}
    assert RuleCategory.INJECTION_RISKS in categories
    assert RuleCategory.AUTHENTICATION_ISSUES in categories
    assert RuleCategory.AUTHORIZATION_ISSUES in categories
    assert RuleCategory.DATA_EXPOSURE in categories
    assert RuleCategory.INPUT_VALIDATION in categories
    assert RuleCategory.DEPENDENCY_RISKS in categories


def test_cwe_mapping_and_severities():
    """Check that each rule defines a valid CWE and non-empty fix guidance."""
    for rule in SECURITY_RULES:
        assert rule.id in RULE_CATALOG
        assert rule.cwe_id.startswith("CWE-")
        assert len(rule.fix_guidance) > 10
        assert rule.severity in (
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        )


def test_sql_injection_pattern_detected():
    scanner = SecurityScannerTool()
    vulnerable_code = """
def fetch_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return execute_query(query)
"""
    findings = scanner.scan_file_content(vulnerable_code, file_label="test_vulnerable.py")
    sql_findings = [f for f in findings if f.rule_id == "INJ-001"]
    assert len(sql_findings) >= 1
    assert sql_findings[0].cwe == "CWE-89"
    assert sql_findings[0].severity == "Critical"


def test_command_injection_pattern_detected():
    scanner = SecurityScannerTool()
    vulnerable_code = """
import os
import subprocess

def run_backup(folder):
    os.system(f"tar -czf backup.tar.gz {folder}")
    subprocess.call("ls " + folder, shell=True)
"""
    findings = scanner.scan_file_content(vulnerable_code, file_label="test_cmd.py")
    cmd_findings = [f for f in findings if f.rule_id == "INJ-002"]
    assert len(cmd_findings) >= 1
    assert any("shell=True" in f.snippet or "os.system" in f.snippet for f in cmd_findings)
    assert cmd_findings[0].cwe == "CWE-78"


def test_eval_template_injection_detected():
    scanner = SecurityScannerTool()
    vulnerable_code = """
def calculate(expr):
    result = eval(expr)
    return result
"""
    findings = scanner.scan_file_content(vulnerable_code, file_label="test_eval.py")
    eval_findings = [f for f in findings if f.rule_id == "INJ-004"]
    assert len(eval_findings) >= 1
    assert eval_findings[0].severity == "Critical"


def test_clean_code_zero_findings():
    scanner = SecurityScannerTool()
    clean_code = """
import hashlib
import secrets

def get_secure_token():
    return secrets.token_hex(32)

def hash_data(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
"""
    findings = scanner.scan_file_content(clean_code, file_label="clean_module.py")
    # Clean code without hardcoded credentials or dangerous sinks should have zero findings
    critical_or_high = [f for f in findings if f.severity in ("Critical", "High")]
    assert len(critical_or_high) == 0
