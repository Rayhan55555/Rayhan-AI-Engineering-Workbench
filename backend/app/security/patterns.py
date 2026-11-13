import re

# ==============================================================================
# 1. INJECTION PATTERNS
# ==============================================================================

# SQL injection: string formatting inside SQL queries or f-strings with SQL keywords
SQL_INJECTION_FORMAT = re.compile(
    r"""(?i)\b(?:select|insert|update|delete|drop|alter)\b.*?(\{.*?\}|%s|\.format\(|\+\s*[a-zA-Z_])""",
    re.MULTILINE,
)

# Command injection: shell=True or direct os.system/popen
COMMAND_INJECTION_SHELL = re.compile(
    r"""(?i)(?:subprocess\.(?:Popen|call|run|check_output|check_call)\(.*?\bshell\s*=\s*True|os\.system\(|os\.popen\()""",
    re.MULTILINE,
)

# Path traversal: concatenation of user input into filesystem operations
PATH_TRAVERSAL_CONCAT = re.compile(
    r"""(?:open|Path)\s*\(\s*(?:f["'].*?\{|.*?\+\s*).*?\.\./""",
    re.MULTILINE,
)

# Template injection (eval / exec with variable)
TEMPLATE_INJECTION_EVAL = re.compile(
    r"""\b(?:eval|exec)\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)""",
)

# ==============================================================================
# 2. SECRET DETECTION PATTERNS
# ==============================================================================

# AWS Access Key ID (AKIA...)
AWS_KEY_PATTERN = re.compile(r"""\b(AKIA[0-9A-Z]{16})\b""")

# Generic API Key assignments (api_key = "...")
GENERIC_API_KEY_PATTERN = re.compile(
    r"""(?i)(?:api_key|apikey|secret_key|app_secret|client_secret)\s*=\s*["']([a-zA-Z0-9_\-]{16,})["']"""
)

# Hardcoded JWT secrets (jwt_secret = "...")
JWT_SECRET_PATTERN = re.compile(
    r"""(?i)(?:jwt_secret|jwt_key|token_secret)\s*=\s*["']([^"'\s]{8,})["']"""
)

# Hardcoded passwords (password = "...")
PASSWORD_ASSIGNMENT_PATTERN = re.compile(
    r"""(?i)(?:password|passwd|pwd)\s*=\s*["']([^"'\s]{6,})["']"""
)

# Database URLs with embedded credentials
DATABASE_URL_CREDENTIALS = re.compile(
    r"""(?:postgres|postgresql|mysql|sqlite)://[a-zA-Z0-9_]+:([^@\s]+)@"""
)

# Private Key Headers
PRIVATE_KEY_HEADER = re.compile(
    r"""-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"""
)

# Hardcoded Bearer Tokens
BEARER_TOKEN_PATTERN = re.compile(
    r"""(?i)bearer\s+["']?([a-zA-Z0-9_\-\.]{20,})["']?"""
)

# Weak JWT Algorithm (alg=none)
JWT_ALG_NONE_PATTERN = re.compile(
    r"""(?i)["']algorithm["']\s*:\s*["']none["']|algorithms\s*=\s*\[\s*["']none["']\s*\]"""
)

# ==============================================================================
# 3. DATA EXPOSURE PATTERNS
# ==============================================================================

# Sensitive data logged (logging password / token / secret)
LOGGING_SENSITIVE_DATA = re.compile(
    r"""(?i)(?:logger|logging)\.(?:debug|info|warning|error|exception)\(.*?\b(?:password|secret|token|api_key|credit_card)\b"""
)

# Stack trace returned in response
STACK_TRACE_IN_RESPONSE = re.compile(
    r"""(?i)(?:traceback\.format_exc\(\)|traceback\.print_exc\(\)).*?(?:return|response|raise)"""
)

# ==============================================================================
# 4. INPUT VALIDATION & WEAK CRYPTO PATTERNS
# ==============================================================================

# Weak hashing (MD5 or SHA1 for passwords / signatures)
WEAK_HASHING_ALGORITHM = re.compile(
    r"""\b(?:hashlib\.md5|hashlib\.sha1)\s*\("""
)

# Insecure random number generator for cryptographic use
INSECURE_RANDOM = re.compile(
    r"""\b(?:random\.random|random\.randint|random\.choice)\s*\("""
)

# Dangerous YAML load (yaml.load without Loader)
INSECURE_YAML_LOAD = re.compile(
    r"""\byaml\.load\s*\([^,)]+\)"""
)
