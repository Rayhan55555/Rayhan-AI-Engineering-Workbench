import pytest
from backend.app.tools.secret_detector import SecretDetectorTool, mask_secret


def test_mask_secret_helper():
    assert mask_secret("sk-1234567890abcdef") == "sk-1****"
    assert mask_secret("AKIAIOSFODNN7EXAMPLE") == "AKIA****"
    assert mask_secret("123") == "****"
    # Ensure sensitive tail is never leaked
    assert "abcdef" not in mask_secret("sk-1234567890abcdef")


def test_aws_access_key_detected_and_masked():
    detector = SecretDetectorTool()
    sample = """
AWS_KEY = "AKIA1234567890ABCDEF"
REGION = "us-east-1"
"""
    findings = detector.scan_content(sample, file_label="config.py")
    assert len(findings) == 1
    f = findings[0]
    assert f.pattern_type == "aws_access_key"
    assert f.masked_preview == "AKIA****"
    assert "ABCDEF" not in f.masked_preview
    assert f.severity == "Critical"
    assert f.cwe_id == "CWE-798"


def test_hardcoded_jwt_secret_detected_and_masked():
    detector = SecretDetectorTool()
    sample = """
JWT_SECRET = "supersecretjwtkeythatshouldnotbecommitted"
ALGORITHM = "HS256"
"""
    findings = detector.scan_content(sample, file_label="jwt_config.py")
    assert len(findings) >= 1
    jwt_findings = [f for f in findings if f.pattern_type == "jwt_secret"]
    assert len(jwt_findings) == 1
    assert jwt_findings[0].masked_preview == "supe****"
    assert "shouldnotbecommitted" not in jwt_findings[0].masked_preview


def test_database_url_credentials_masked():
    detector = SecretDetectorTool()
    sample = """
DATABASE_URL = "postgresql://dbuser:supersecretpass123@localhost:5432/mydb"
"""
    findings = detector.scan_content(sample, file_label="db.py")
    assert len(findings) == 1
    assert "supersecretpass123" not in findings[0].masked_preview
    assert findings[0].pattern_type == "database_credentials"


def test_private_key_header_detected():
    detector = SecretDetectorTool()
    sample = """
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3
-----END PRIVATE KEY-----
"""
    findings = detector.scan_content(sample, file_label="server.key")
    assert len(findings) >= 1
    assert findings[0].pattern_type == "private_key"
    assert "MIIE" not in findings[0].masked_preview


def test_clean_file_zero_secrets():
    detector = SecretDetectorTool()
    clean = """
import os
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
"""
    findings = detector.scan_content(clean, file_label="safe_config.py")
    assert len(findings) == 0
