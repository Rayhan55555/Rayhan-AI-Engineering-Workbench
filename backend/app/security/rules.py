import ast
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel
from backend.app.security.patterns import (
    AWS_KEY_PATTERN,
    BEARER_TOKEN_PATTERN,
    COMMAND_INJECTION_SHELL,
    DATABASE_URL_CREDENTIALS,
    GENERIC_API_KEY_PATTERN,
    INSECURE_RANDOM,
    INSECURE_YAML_LOAD,
    JWT_ALG_NONE_PATTERN,
    JWT_SECRET_PATTERN,
    LOGGING_SENSITIVE_DATA,
    PASSWORD_ASSIGNMENT_PATTERN,
    PATH_TRAVERSAL_CONCAT,
    PRIVATE_KEY_HEADER,
    SQL_INJECTION_FORMAT,
    STACK_TRACE_IN_RESPONSE,
    TEMPLATE_INJECTION_EVAL,
    WEAK_HASHING_ALGORITHM,
)
from backend.app.security.severity import RuleCategory, Severity


class SecurityRule(BaseModel):
    id: str
    category: RuleCategory
    severity: Severity
    title: str
    description: str
    fix_guidance: str
    cwe_id: str
    pattern_type: str = "regex"  # 'regex' or 'ast'


# 18+ Security Rules across 6 distinct categories
SECURITY_RULES: List[SecurityRule] = [
    # --------------------------------------------------------------------------
    # INJECTION RISKS (CWE-89, CWE-78, CWE-22, CWE-94)
    # --------------------------------------------------------------------------
    SecurityRule(
        id="INJ-001",
        category=RuleCategory.INJECTION_RISKS,
        severity=Severity.CRITICAL,
        title="SQL Injection Risk via String Formatting",
        description="SQL queries constructed using string interpolation or concatenation can lead to arbitrary SQL execution.",
        fix_guidance="Use parameterized queries or ORM query abstractions (e.g., SQLAlchemy select/where clauses).",
        cwe_id="CWE-89",
    ),
    SecurityRule(
        id="INJ-002",
        category=RuleCategory.INJECTION_RISKS,
        severity=Severity.CRITICAL,
        title="Command Injection via Shell Execution",
        description="Invoking subprocess with shell=True or direct os.system/os.popen allows shell command chaining.",
        fix_guidance="Use asyncio.create_subprocess_exec or subprocess.run with an explicit list of arguments and shell=False.",
        cwe_id="CWE-78",
    ),
    SecurityRule(
        id="INJ-003",
        category=RuleCategory.INJECTION_RISKS,
        severity=Severity.HIGH,
        title="Path Traversal Risk",
        description="Constructing filesystem paths with unvalidated user input containing '../' may expose sensitive files.",
        fix_guidance="Resolve paths with Path.resolve() and verify they remain strictly inside the designated directory.",
        cwe_id="CWE-22",
    ),
    SecurityRule(
        id="INJ-004",
        category=RuleCategory.INJECTION_RISKS,
        severity=Severity.CRITICAL,
        title="Arbitrary Code Execution via eval/exec",
        description="Passing dynamic variables to eval() or exec() permits arbitrary Python code execution.",
        fix_guidance="Avoid eval/exec; use safe parsing libraries like ast.literal_eval() or json.loads().",
        cwe_id="CWE-94",
    ),

    # --------------------------------------------------------------------------
    # AUTHENTICATION ISSUES (CWE-798, CWE-347, CWE-287, CWE-328)
    # --------------------------------------------------------------------------
    SecurityRule(
        id="AUTH-001",
        category=RuleCategory.AUTHENTICATION_ISSUES,
        severity=Severity.CRITICAL,
        title="Hardcoded Secret or AWS Key Detected",
        description="Hardcoded secrets, API tokens, or AWS credentials checked into code compromise system security.",
        fix_guidance="Store secrets exclusively in environment variables or a secrets manager, injected at runtime.",
        cwe_id="CWE-798",
    ),
    SecurityRule(
        id="AUTH-002",
        category=RuleCategory.AUTHENTICATION_ISSUES,
        severity=Severity.HIGH,
        title="Hardcoded Password Assignment",
        description="Passwords assigned directly in source code violate credential storage standards.",
        fix_guidance="Prompt users for passwords, hash them with bcrypt, and never commit static credentials.",
        cwe_id="CWE-798",
    ),
    SecurityRule(
        id="AUTH-003",
        category=RuleCategory.AUTHENTICATION_ISSUES,
        severity=Severity.CRITICAL,
        title="Insecure JWT None Algorithm",
        description="Allowing algorithm='none' in JWT validation disables cryptographic token signature verification.",
        fix_guidance="Explicitly require robust algorithms such as HS256, RS256, or ES256 and forbid 'none'.",
        cwe_id="CWE-347",
    ),
    SecurityRule(
        id="AUTH-004",
        category=RuleCategory.AUTHENTICATION_ISSUES,
        severity=Severity.HIGH,
        title="Hardcoded JWT Secret Key",
        description="Static JWT secrets embedded in code permit token forgery by unauthorized parties.",
        fix_guidance="Load the JWT secret from environment configuration (e.g., settings.SECRET_KEY).",
        cwe_id="CWE-798",
    ),

    # --------------------------------------------------------------------------
    # AUTHORIZATION ISSUES (CWE-862, CWE-639, CWE-269)
    # --------------------------------------------------------------------------
    SecurityRule(
        id="AUTHZ-001",
        category=RuleCategory.AUTHORIZATION_ISSUES,
        severity=Severity.HIGH,
        title="Unprotected Write Endpoint (Missing Auth Dependency)",
        description="Mutating API endpoint (POST/PUT/DELETE) is defined without Depends(get_current_user).",
        fix_guidance="Add authenticated user dependency 'current_user: User = Depends(get_current_user)' to endpoint signature.",
        cwe_id="CWE-862",
    ),
    SecurityRule(
        id="AUTHZ-002",
        category=RuleCategory.AUTHORIZATION_ISSUES,
        severity=Severity.HIGH,
        title="Insecure Direct Object Reference (IDOR) Pattern",
        description="Endpoint retrieves records by ID without validating ownership or checking tenant isolation.",
        fix_guidance="Enforce an ownership check: verify resource.user_id == current_user.id before returning data.",
        cwe_id="CWE-639",
    ),
    SecurityRule(
        id="AUTHZ-003",
        category=RuleCategory.AUTHORIZATION_ISSUES,
        severity=Severity.MEDIUM,
        title="Missing Privilege Escalation Guard",
        description="Administrative endpoints or role modifications must verify is_superuser status.",
        fix_guidance="Guard privileged actions with 'Depends(get_current_superuser)'.",
        cwe_id="CWE-269",
    ),

    # --------------------------------------------------------------------------
    # DATA EXPOSURE (CWE-532, CWE-209, CWE-312)
    # --------------------------------------------------------------------------
    SecurityRule(
        id="DATA-001",
        category=RuleCategory.DATA_EXPOSURE,
        severity=Severity.HIGH,
        title="Sensitive Data Logged",
        description="Logging passwords, tokens, API keys, or secret headers exposes credentials in log storage.",
        fix_guidance="Sanitize or redact sensitive fields before sending payloads to logging outputs.",
        cwe_id="CWE-532",
    ),
    SecurityRule(
        id="DATA-002",
        category=RuleCategory.DATA_EXPOSURE,
        severity=Severity.MEDIUM,
        title="Stack Trace Exposed in API Response",
        description="Returning internal traceback details in API responses leaks server architecture and libraries.",
        fix_guidance="Catch exceptions internally and return generic, user-safe error messages with request IDs.",
        cwe_id="CWE-209",
    ),
    SecurityRule(
        id="DATA-003",
        category=RuleCategory.DATA_EXPOSURE,
        severity=Severity.HIGH,
        title="Private Key Header Detected",
        description="Private key material (e.g. RSA or OPENSSH PRIVATE KEY) detected in repository files.",
        fix_guidance="Remove private keys immediately and rotate any associated certificates.",
        cwe_id="CWE-312",
    ),

    # --------------------------------------------------------------------------
    # INPUT VALIDATION & WEAK CRYPTO (CWE-20, CWE-328, CWE-330, CWE-502)
    # --------------------------------------------------------------------------
    SecurityRule(
        id="INP-001",
        category=RuleCategory.INPUT_VALIDATION,
        severity=Severity.MEDIUM,
        title="Weak Hashing Algorithm (MD5/SHA1)",
        description="MD5 and SHA-1 are cryptographically broken and prone to collision attacks.",
        fix_guidance="Use SHA-256 or SHA-512 for signatures, and bcrypt or argon2 for password hashing.",
        cwe_id="CWE-328",
    ),
    SecurityRule(
        id="INP-002",
        category=RuleCategory.INPUT_VALIDATION,
        severity=Severity.MEDIUM,
        title="Insecure Pseudo-Random Generator for Security",
        description="Standard random module is predictable and should not be used for security tokens or nonces.",
        fix_guidance="Use python stdlib 'secrets' module (e.g. secrets.token_hex) for cryptographically secure randomness.",
        cwe_id="CWE-330",
    ),
    SecurityRule(
        id="INP-003",
        category=RuleCategory.INPUT_VALIDATION,
        severity=Severity.HIGH,
        title="Insecure YAML Deserialization",
        description="yaml.load() without a SafeLoader allows arbitrary object instantiation and code execution.",
        fix_guidance="Use yaml.safe_load() instead of yaml.load().",
        cwe_id="CWE-502",
    ),

    # --------------------------------------------------------------------------
    # DEPENDENCY RISKS (CWE-1104, CWE-1035)
    # --------------------------------------------------------------------------
    SecurityRule(
        id="DEP-001",
        category=RuleCategory.DEPENDENCY_RISKS,
        severity=Severity.HIGH,
        title="Known Vulnerable Package Version Range",
        description="Dependency declared with a version range known to contain high-severity security vulnerabilities.",
        fix_guidance="Upgrade package to the latest patched release or pin safe semantic version.",
        cwe_id="CWE-1104",
    ),
    SecurityRule(
        id="DEP-002",
        category=RuleCategory.DEPENDENCY_RISKS,
        severity=Severity.LOW,
        title="Unpinned Major Dependency Version",
        description="Packages declared without pinned versions (e.g. bare package name) can introduce unvetted breaking changes.",
        fix_guidance="Pin dependencies with specific versions or compatible release specifiers (e.g., package>=1.0.0,<2.0.0).",
        cwe_id="CWE-1035",
    ),
]

RULE_CATALOG: Dict[str, SecurityRule] = {r.id: r for r in SECURITY_RULES}
