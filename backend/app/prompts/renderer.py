from pathlib import Path
from typing import Any, Dict, Optional
import jinja2

TEMPLATES_DIR = Path(__file__).parent / "templates"


class PromptRenderer:
    """
    Renders Jinja2 prompts safely for each agent.
    Falls back gracefully to formatted strings if template rendering fails.
    """
    def __init__(self, templates_dir: Optional[Path] = None):
        self.dir = templates_dir or TEMPLATES_DIR
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        # Sanitize sensitive keys from context values
        safe_context = self._sanitize_context(context)
        try:
            template = self.env.get_template(template_name)
            return template.render(**safe_context)
        except Exception:
            # Fallback simple render
            base_msg = safe_context.get("instruction", "No instruction provided.")
            return f"Agent Task: {base_msg}\nContext: {safe_context}"

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for k, v in context.items():
            if isinstance(v, str):
                # Clean API keys or injection patterns
                clean_val = v
                for pat in ("AIza", "sk-ant-", "sk-proj-"):
                    if pat in clean_val:
                        clean_val = "[MASKED_KEY]"
                sanitized[k] = clean_val
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize_context(v)
            else:
                sanitized[k] = v
        return sanitized
