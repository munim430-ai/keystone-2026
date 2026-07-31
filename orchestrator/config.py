"""Central config — env-driven, safe defaults, $0 by default.

Every knob defaults to the free/offline path: mock LLM, NocoDB dry-run,
no sending. Real endpoints activate only when the founder sets keys.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# repo layout ---------------------------------------------------------------
ORCH_DIR = Path(__file__).resolve().parent
REPO_DIR = ORCH_DIR.parent
AUDIT_DIR = REPO_DIR / "audit-system"
STUDENTS_DIR = AUDIT_DIR / "students"          # extend the EXISTING convention
MANIFEST_DIR = AUDIT_DIR / "manifests"
TEMPLATE_METADATA = STUDENTS_DIR / "_TEMPLATE" / "metadata.yaml"
MASTER_LIST = REPO_DIR / "data" / "Korea_Master_University_List.xlsx"
TEMPLATES_DIR = ORCH_DIR / "templates"

# LLM endpoints the system is allowed to call. Anything else is refused by
# guardrails (open-source / zero-spend rule). Groq has a free tier; Ollama is
# local; mock needs nothing.
LLM_ALLOWLIST = (
    "https://api.groq.com/openai/v1",
    "http://localhost:11434",       # Ollama default
    "http://127.0.0.1:11434",
    "mock",
)


def _b(name: str, default: bool) -> bool:
    v = os.getenv(name, "").strip().lower()
    return default if not v else v in ("1", "true", "yes", "on")


def _s(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip() or default


def _i(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


@dataclass
class Config:
    # LLM
    llm_provider: str = field(default_factory=lambda: _s("KEYSTONE_LLM", "auto"))  # auto|groq|ollama|mock
    groq_api_key: str = field(default_factory=lambda: _s("GROQ_API_KEY"))
    groq_model: str = field(default_factory=lambda: _s("GROQ_MODEL", "llama-3.3-70b-versatile"))
    ollama_model: str = field(default_factory=lambda: _s("OLLAMA_MODEL", "llama3.1"))
    ollama_url: str = field(default_factory=lambda: _s("OLLAMA_URL", "http://localhost:11434"))

    # NocoDB (dry-run unless all three set)
    nocodb_base_url: str = field(default_factory=lambda: _s("NOCODB_BASE_URL"))
    nocodb_token: str = field(default_factory=lambda: _s("NOCODB_TOKEN"))
    nocodb_students_table: str = field(default_factory=lambda: _s("NOCODB_STUDENTS_TABLE"))
    nocodb_drafts_table: str = field(default_factory=lambda: _s("NOCODB_DRAFTS_TABLE"))

    # survival clock (from keystone-reality-plan-2026.md kill criteria)
    survival_target_per_month: int = field(default_factory=lambda: _i("SURVIVAL_TARGET", 2))

    server_host: str = field(default_factory=lambda: _s("HOST", "127.0.0.1"))
    server_port: int = field(default_factory=lambda: _i("PORT", 8090))

    @property
    def nocodb_live(self) -> bool:
        return bool(self.nocodb_base_url and self.nocodb_token and self.nocodb_students_table)

    def resolve_llm(self) -> str:
        if self.llm_provider != "auto":
            return self.llm_provider
        if self.groq_api_key:
            return "groq"
        return "mock"  # never assume Ollama is running; mock guarantees $0 + offline


CFG = Config()
