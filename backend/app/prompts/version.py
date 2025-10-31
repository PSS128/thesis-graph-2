"""
Prompt versioning system to track prompt effectiveness and enable A/B testing.

Each prompt type has a version string and changelog. Versions are included in:
- Cache keys (allows testing different prompt versions)
- API response headers (for debugging and analytics)
- LLM metrics logging (track performance by version)
"""

from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptVersion:
    """Metadata for a prompt version."""
    version: str
    date_introduced: str
    changes: str
    is_active: bool = True


class PromptVersions:
    """Central registry of all prompt versions."""

    # Node Extraction Versions
    NODE_EXTRACTION_VERSION = "2.0.0"
    NODE_EXTRACTION_CHANGELOG: Dict[str, PromptVersion] = {
        "2.0.0": PromptVersion(
            version="2.0.0",
            date_introduced="2025-10-29",
            changes="Advanced prompts with domain-specific guidance, quality criteria, and extended schema",
            is_active=True
        ),
        "1.0.0": PromptVersion(
            version="1.0.0",
            date_introduced="2025-01-01",
            changes="Initial basic extraction prompt",
            is_active=False
        ),
    }

    # Edge Rationale Versions
    EDGE_RATIONALE_VERSION = "2.0.0"
    EDGE_RATIONALE_CHANGELOG: Dict[str, PromptVersion] = {
        "2.0.0": PromptVersion(
            version="2.0.0",
            date_introduced="2025-10-29",
            changes="Advanced causal inference framework with mechanisms, assumptions, confounders, evidence hierarchy",
            is_active=True
        ),
        "1.0.0": PromptVersion(
            version="1.0.0",
            date_introduced="2025-01-01",
            changes="Initial basic rationale prompt",
            is_active=False
        ),
    }

    # Composition Versions
    COMPOSITION_VERSION = "1.1.0"
    COMPOSITION_CHANGELOG: Dict[str, PromptVersion] = {
        "1.1.0": PromptVersion(
            version="1.1.0",
            date_introduced="2025-10-29",
            changes="Enhanced citation format enforcement with examples, added Limitations & Counterarguments section",
            is_active=True
        ),
        "1.0.0": PromptVersion(
            version="1.0.0",
            date_introduced="2025-01-01",
            changes="Initial composition prompt with outline and essay generation",
            is_active=False
        ),
    }

    # Evidence Retrieval Versions
    EVIDENCE_VERSION = "1.0.0"
    EVIDENCE_CHANGELOG: Dict[str, PromptVersion] = {
        "1.0.0": PromptVersion(
            version="1.0.0",
            date_introduced="2025-01-01",
            changes="Initial evidence retrieval implementation",
            is_active=True
        ),
    }

    @classmethod
    def get_version(cls, prompt_type: str) -> str:
        """Get the active version for a prompt type."""
        version_map = {
            "node_extraction": cls.NODE_EXTRACTION_VERSION,
            "edge_rationale": cls.EDGE_RATIONALE_VERSION,
            "composition": cls.COMPOSITION_VERSION,
            "evidence": cls.EVIDENCE_VERSION,
        }
        return version_map.get(prompt_type, "1.0.0")

    @classmethod
    def get_changelog(cls, prompt_type: str) -> Dict[str, PromptVersion]:
        """Get the full changelog for a prompt type."""
        changelog_map = {
            "node_extraction": cls.NODE_EXTRACTION_CHANGELOG,
            "edge_rationale": cls.EDGE_RATIONALE_CHANGELOG,
            "composition": cls.COMPOSITION_CHANGELOG,
            "evidence": cls.EVIDENCE_CHANGELOG,
        }
        return changelog_map.get(prompt_type, {})

    @classmethod
    def get_all_versions(cls) -> Dict[str, str]:
        """Get active versions for all prompt types."""
        return {
            "node_extraction": cls.NODE_EXTRACTION_VERSION,
            "edge_rationale": cls.EDGE_RATIONALE_VERSION,
            "composition": cls.COMPOSITION_VERSION,
            "evidence": cls.EVIDENCE_VERSION,
        }

    @classmethod
    def get_version_info(cls, prompt_type: str, version: str) -> PromptVersion:
        """Get detailed info for a specific version."""
        changelog = cls.get_changelog(prompt_type)
        return changelog.get(version)


def make_cache_key_with_version(prompt_type: str, *args) -> tuple:
    """
    Create a cache key that includes the prompt version.
    This allows different prompt versions to have separate caches for A/B testing.

    Example:
        key = make_cache_key_with_version("node_extraction", text, domain)
        # Returns: ("node_extraction", "2.0.0", text, domain)
    """
    version = PromptVersions.get_version(prompt_type)
    return (prompt_type, version, *args)


def get_version_header(prompt_type: str) -> str:
    """
    Get formatted version header for API responses.

    Example:
        header = get_version_header("composition")
        # Returns: "composition:1.1.0"
    """
    version = PromptVersions.get_version(prompt_type)
    return f"{prompt_type}:{version}"
