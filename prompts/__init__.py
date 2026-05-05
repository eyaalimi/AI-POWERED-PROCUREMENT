"""
prompts — Versioned prompt loader.
Load prompts from markdown files, stripping the header comments.
"""
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(filename: str) -> str:
    """Load a prompt file and strip leading comment lines (# ...)."""
    path = PROMPTS_DIR / filename
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    # Skip header comment lines at the top
    content_lines = []
    header_done = False
    for line in lines:
        if not header_done and line.startswith("#"):
            continue
        header_done = True
        content_lines.append(line)
    return "\n".join(content_lines).strip()


# Pre-loaded prompts for easy import
ANALYSIS_PROMPT = load_prompt("analysis_v1.0.md")
SOURCING_PROMPT = load_prompt("sourcing_v1.0.md")
COMMUNICATION_RFQ_PROMPT = load_prompt("communication_rfq_v1.0.md")
ORCHESTRATOR_PROMPT = load_prompt("orchestrator_v1.0.md")
