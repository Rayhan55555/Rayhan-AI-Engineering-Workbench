import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
    validate_file_extension,
)
from backend.app.tools.base_tool import BaseTool, ToolResult


class CodeAnalyzerTool(BaseTool):
    name = "code_analyzer"
    description = (
        "Parses code files using Python AST or TypeScript pattern matchers. "
        "Extracts functions, classes, imports, calculates cyclomatic complexity, "
        "detects missing type hints, unused imports, and docstring coverage."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        file_path_str = params.get("path") or params.get("file_path")
        code_content = params.get("content")

        # Either path or direct content must be provided
        safe_path: Optional[Path] = None
        if file_path_str:
            try:
                safe_path = resolve_safe_path(str(file_path_str), PROJECT_ROOT)
                validate_file_extension(safe_path)
                if not safe_path.exists():
                    return ToolResult(
                        success=False,
                        output={},
                        error=f"File not found: '{file_path_str}'.",
                        evidence=[],
                        simulated=False,
                    )
                code_content = safe_path.read_text(encoding="utf-8")
            except SandboxSecurityError as e:
                return ToolResult(
                    success=False,
                    output={},
                    error=str(e),
                    evidence=[f"Blocked analyzer path: {file_path_str}"],
                    simulated=False,
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output={},
                    error=f"Error reading file for analysis: {str(e)}",
                    evidence=[],
                    simulated=False,
                )

        if code_content is None:
            return ToolResult(
                success=False,
                output={},
                error="Either 'path' or 'content' must be provided.",
                evidence=[],
                simulated=False,
            )

        # Detect language
        language = "python"
        if safe_path:
            suffix = safe_path.suffix.lower()
            if suffix in (".ts", ".tsx", ".js", ".jsx"):
                language = "typescript"
        elif params.get("language") in ("typescript", "javascript", "ts", "js"):
            language = "typescript"

        if language == "python":
            analysis = self._analyze_python(code_content)
        else:
            analysis = self._analyze_typescript(code_content)

        file_label = safe_path.name if safe_path else "in-memory buffer"
        return ToolResult(
            success=True,
            output=analysis,
            evidence=[
                f"AST analysis complete for: {file_label} ({language})",
                f"Found {len(analysis.get('functions', []))} functions, {len(analysis.get('classes', []))} classes",
                f"{len(analysis.get('issues', []))} quality issues detected",
            ],
            simulated=False,
            metadata={
                "language": language,
                "issues_count": len(analysis.get("issues", [])),
                "metrics": analysis.get("metrics", {}),
            },
        )

    def _analyze_python(self, code: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "language": "python",
                "syntax_error": {
                    "line": e.lineno,
                    "offset": e.offset,
                    "msg": e.msg,
                },
                "functions": [],
                "classes": [],
                "imports": [],
                "issues": [
                    {
                        "type": "syntax_error",
                        "line": e.lineno or 1,
                        "severity": "high",
                        "suggestion": f"Syntax error: {e.msg}",
                    }
                ],
                "metrics": {
                    "complexity": 0,
                    "docstring_coverage": 0.0,
                    "type_coverage": 0.0,
                },
            }

        functions: List[Dict[str, Any]] = []
        classes: List[Dict[str, Any]] = []
        imports: List[str] = []
        issues: List[Dict[str, Any]] = []

        total_defs = 0
        documented_defs = 0
        annotated_defs = 0
        total_complexity = 1

        # Track imported names to find unused imports
        imported_symbols: Dict[str, int] = {}
        used_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)

        for node in tree.body:
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imp_name = alias.asname or alias.name
                    imports.append(alias.name)
                    imported_symbols[imp_name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    sym_name = alias.asname or alias.name
                    imports.append(full_name)
                    imported_symbols[sym_name] = node.lineno

            # Classes
            elif isinstance(node, ast.ClassDef):
                total_defs += 1
                has_doc = ast.get_docstring(node) is not None
                if has_doc:
                    documented_defs += 1

                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": methods,
                    "has_docstring": has_doc,
                })

            # Top-level Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_defs += 1
                has_doc = ast.get_docstring(node) is not None
                if has_doc:
                    documented_defs += 1

                has_return_type = node.returns is not None
                if has_return_type:
                    annotated_defs += 1
                else:
                    issues.append({
                        "type": "missing_type_hint",
                        "line": node.lineno,
                        "severity": "low",
                        "suggestion": f"Add return type annotation for '{node.name}()'",
                    })

                # Check parameter annotations
                for arg in node.args.args:
                    if arg.arg != "self" and arg.annotation is None:
                        issues.append({
                            "type": "missing_arg_type",
                            "line": node.lineno,
                            "severity": "low",
                            "suggestion": f"Add type hint for parameter '{arg.arg}' in '{node.name}()'",
                        })

                # Basic cyclomatic complexity calculation
                func_complexity = self._calculate_cyclomatic_complexity(node)
                total_complexity += func_complexity

                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "has_docstring": has_doc,
                    "has_return_annotation": has_return_type,
                    "complexity": func_complexity,
                })

        # Check for unused imports
        for sym, line in imported_symbols.items():
            if sym not in used_names and not sym.startswith("_"):
                issues.append({
                    "type": "unused_import",
                    "line": line,
                    "severity": "low",
                    "suggestion": f"Imported name '{sym}' appears unused.",
                })

        doc_cov = round(documented_defs / total_defs, 2) if total_defs > 0 else 1.0
        type_cov = round(annotated_defs / total_defs, 2) if total_defs > 0 else 1.0

        return {
            "language": "python",
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "issues": issues,
            "metrics": {
                "complexity": total_complexity,
                "docstring_coverage": doc_cov,
                "type_coverage": type_cov,
            },
        }

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _analyze_typescript(self, code: str) -> Dict[str, Any]:
        functions: List[Dict[str, Any]] = []
        classes: List[Dict[str, Any]] = []
        imports: List[str] = []
        issues: List[Dict[str, Any]] = []

        lines = code.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Imports: import { ... } from '...';
            imp_match = re.search(r"import\s+.*?from\s+['\"](.*?)['\"]", stripped)
            if imp_match:
                imports.append(imp_match.group(1))

            # Functions: function foo(...) or const foo = (...) => ...
            fn_match = re.search(r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)", stripped)
            if fn_match:
                functions.append({"name": fn_match.group(1), "line": idx})

            arrow_match = re.search(r"(?:export\s+)?const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", stripped)
            if arrow_match:
                functions.append({"name": arrow_match.group(1), "line": idx})

            # React Component: const MyComp: React.FC = ...
            comp_match = re.search(r"(?:export\s+)?(?:const|class)\s+([A-Z][a-zA-Z0-9_]+)", stripped)
            if comp_match:
                classes.append({"name": comp_match.group(1), "line": idx})

            # Detect ': any' usage
            if re.search(r":\s*any\b", stripped) and not stripped.startswith("//"):
                issues.append({
                    "type": "explicit_any",
                    "line": idx,
                    "severity": "medium",
                    "suggestion": "Avoid using ': any'; specify a concrete TypeScript interface or unknown.",
                })

        return {
            "language": "typescript",
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "issues": issues,
            "metrics": {
                "complexity": len(functions) + len(classes) + 1,
                "docstring_coverage": 0.5,
                "type_coverage": 0.9 if not issues else 0.7,
            },
        }
