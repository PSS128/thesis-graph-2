"""
Tests for prompt functionality and LLM integration.

Run with:
    pytest tests/test_prompts.py
    pytest tests/test_prompts.py -v
    pytest tests/test_prompts.py -k "test_citation" # Run specific test
    pytest tests/test_prompts.py -m unit  # Run only unit tests
"""

import pytest
import json
import re
from unittest.mock import patch, MagicMock

# Import functions to test
from app.services.llm import (
    _validate_citation_format,
    _extract_json_strict,
    _extract_json_relaxed,
    _strip_code_fences,
    _normalize_quotes,
)
from app.prompts.version import PromptVersions, make_cache_key_with_version, get_version_header


# ============================================================================
# Prompt Versioning Tests
# ============================================================================

@pytest.mark.unit
def test_get_version_returns_correct_version():
    """Test that get_version returns the expected version string."""
    version = PromptVersions.get_version("composition")
    assert version == "1.1.0"

    version = PromptVersions.get_version("node_extraction")
    assert version == "2.0.0"

    version = PromptVersions.get_version("edge_rationale")
    assert version == "2.0.0"


@pytest.mark.unit
def test_get_all_versions():
    """Test that get_all_versions returns all prompt types."""
    versions = PromptVersions.get_all_versions()

    assert "composition" in versions
    assert "node_extraction" in versions
    assert "edge_rationale" in versions
    assert "evidence" in versions

    # Check that all versions are strings
    for version in versions.values():
        assert isinstance(version, str)
        assert re.match(r"\d+\.\d+\.\d+", version)  # Semantic versioning format


@pytest.mark.unit
def test_make_cache_key_with_version():
    """Test that cache keys include version."""
    key = make_cache_key_with_version("composition", "thesis", "nodes", 700)

    # Should be tuple: (prompt_type, version, *args)
    assert isinstance(key, tuple)
    assert key[0] == "composition"
    assert key[1] == "1.1.0"
    assert "thesis" in key
    assert "nodes" in key
    assert 700 in key


@pytest.mark.unit
def test_get_version_header():
    """Test version header formatting."""
    header = get_version_header("composition")
    assert header == "composition:1.1.0"

    header = get_version_header("node_extraction")
    assert header == "node_extraction:2.0.0"


# ============================================================================
# Citation Format Validation Tests
# ============================================================================

@pytest.mark.unit
def test_citation_format_correct():
    """Test that correct citation format passes validation."""
    essay = 'Studies show burnout decreased [Evidence: "employees reported 40% less exhaustion"].'
    is_valid, warnings = _validate_citation_format(essay)

    assert is_valid is True
    assert len(warnings) == 0


@pytest.mark.unit
def test_citation_format_multiple_correct():
    """Test multiple correct citations."""
    essay = '''
    Economic growth accelerated [Evidence: "GDP rose 3.2% in Q4"] during this period.
    Performance improved [Evidence: "productivity increased while maintaining quality"].
    '''
    is_valid, warnings = _validate_citation_format(essay)

    assert is_valid is True
    assert len(warnings) == 0


@pytest.mark.unit
def test_citation_format_numbered_wrong():
    """Test that numbered citations are detected as wrong."""
    essay = "Studies show this result [1] and that result [2]."
    is_valid, warnings = _validate_citation_format(essay)

    assert len(warnings) > 0
    assert any("numbered citations" in w.lower() for w in warnings)


@pytest.mark.unit
def test_citation_format_author_year_wrong():
    """Test that author-year citations are detected as wrong."""
    essay = "Studies show this result (Smith 2024) and that result (Jones 2023)."
    is_valid, warnings = _validate_citation_format(essay)

    assert len(warnings) > 0
    assert any("author-year" in w.lower() for w in warnings)


@pytest.mark.unit
def test_citation_format_evidence_without_quotes():
    """Test that citations without quotes are detected."""
    essay = "Studies show this result [Evidence: no quotes here]."
    is_valid, warnings = _validate_citation_format(essay)

    assert len(warnings) > 0


@pytest.mark.unit
def test_citation_format_empty_text():
    """Test that empty text doesn't cause errors."""
    is_valid, warnings = _validate_citation_format("")
    assert is_valid is True
    assert len(warnings) == 0

    is_valid, warnings = _validate_citation_format(None)
    assert is_valid is True
    assert len(warnings) == 0


# ============================================================================
# JSON Parsing Tests
# ============================================================================

@pytest.mark.unit
def test_strip_code_fences():
    """Test removal of markdown code fences."""
    text = '```json\n{"key": "value"}\n```'
    result = _strip_code_fences(text)
    assert result == '{"key": "value"}'

    text = '```\n{"key": "value"}\n```'
    result = _strip_code_fences(text)
    assert result == '{"key": "value"}'


@pytest.mark.unit
def test_normalize_quotes():
    """Test smart quote normalization."""
    text = '{"key": "value with "smart quotes""}'
    result = _normalize_quotes(text)
    assert '"smart quotes"' in result
    assert '\u201c' not in result
    assert '\u201d' not in result


@pytest.mark.unit
def test_extract_json_strict_valid():
    """Test strict JSON extraction with valid input."""
    text = '{"name": "Test", "value": 123}'
    result = _extract_json_strict(text)

    assert result is not None
    assert result["name"] == "Test"
    assert result["value"] == 123


@pytest.mark.unit
def test_extract_json_strict_with_surrounding_text():
    """Test JSON extraction when surrounded by other text."""
    text = 'Here is some JSON: {"name": "Test", "value": 123} and some more text.'
    result = _extract_json_strict(text)

    assert result is not None
    assert result["name"] == "Test"


@pytest.mark.unit
def test_extract_json_strict_with_code_fences():
    """Test JSON extraction from markdown code fence."""
    text = '```json\n{"name": "Test", "value": 123}\n```'
    result = _extract_json_strict(text)

    assert result is not None
    assert result["name"] == "Test"


@pytest.mark.unit
def test_extract_json_relaxed_with_trailing_commas():
    """Test relaxed JSON extraction handles trailing commas."""
    text = '{"name": "Test", "values": [1, 2, 3,],}'
    result = _extract_json_relaxed(text)

    assert result is not None
    assert result["name"] == "Test"
    assert result["values"] == [1, 2, 3]


@pytest.mark.unit
def test_extract_json_invalid():
    """Test that invalid JSON returns None."""
    text = 'This is not JSON at all'
    result = _extract_json_strict(text)
    assert result is None

    result = _extract_json_relaxed(text)
    assert result is None


# ============================================================================
# Integration Tests (require mocking or real LLM)
# ============================================================================

@pytest.mark.integration
def test_chat_json_with_mock():
    """Test chat_json with mocked LLM response."""
    from app.services.llm import chat_json

    # Mock the _chat function to return a valid JSON string
    with patch('app.services.llm._chat') as mock_chat:
        mock_chat.return_value = ('{"result": "success", "value": 42}', True)

        result = chat_json("system prompt", "user prompt", prompt_type="test")

        assert result is not None
        assert result["result"] == "success"
        assert result["value"] == 42


@pytest.mark.integration
def test_compose_with_mock():
    """Test compose_outline_essay with mocked LLM response."""
    from app.services.llm import compose_outline_essay

    mock_response = {
        "outline": [{"heading": "Introduction", "points": ["Point 1", "Point 2"]}],
        "essay_md": "# Test Essay\n\nThis is a test.",
        "essay_with_citations": '# Test Essay\n\nThis is a test [Evidence: "citation"].'
    }

    with patch('app.services.llm._chat') as mock_chat:
        mock_chat.return_value = (json.dumps(mock_response), True)

        result, used = compose_outline_essay(
            thesis="Test thesis",
            nodes=[{"text": "Node 1", "type": "CLAIM"}],
            edges=[],
            words=500
        )

        assert used is True
        assert "outline" in result
        assert "essay_md" in result
        assert len(result["outline"]) > 0


@pytest.mark.integration
def test_compose_fallback_when_llm_unavailable():
    """Test that compose returns fallback when LLM fails."""
    from app.services.llm import compose_outline_essay

    with patch('app.services.llm._chat') as mock_chat:
        # Simulate LLM failure
        mock_chat.return_value = ("[LLM unavailable]", False)

        result, used = compose_outline_essay(
            thesis="Test thesis",
            nodes=[{"text": "Node 1", "type": "CLAIM"}],
            edges=[],
            words=500
        )

        assert used is False
        assert "outline" in result
        assert "essay_md" in result
        # Should have deterministic fallback
        assert len(result["outline"]) > 0


# ============================================================================
# Node Extraction Tests
# ============================================================================

@pytest.mark.unit
def test_node_extraction_prompt_includes_domain():
    """Test that advanced prompts include domain-specific guidance."""
    from app.prompts.node_extraction import get_extraction_prompts, NodeExtractionContext

    context = NodeExtractionContext(domain="psychology")
    system, user = get_extraction_prompts(
        text="Test text",
        context=context,
        use_advanced=True
    )

    # Should include psychology-specific guidance
    assert "psychology" in system.lower() or "DSM" in system or "validated scales" in system.lower()


@pytest.mark.unit
def test_node_extraction_prompt_basic_vs_advanced():
    """Test that advanced prompts are longer and more detailed."""
    from app.prompts.node_extraction import NodeExtractionPrompts

    basic = NodeExtractionPrompts.get_basic_system()
    advanced = NodeExtractionPrompts.get_advanced_system()

    assert len(advanced) > len(basic)
    assert "quality criteria" in advanced.lower() or "specificity" in advanced.lower()


# ============================================================================
# Edge Rationale Tests
# ============================================================================

@pytest.mark.unit
def test_edge_rationale_prompt_includes_domain():
    """Test that advanced edge prompts include domain guidance."""
    from app.prompts.edge_rationale import get_rationale_prompts, EdgeContext

    context = EdgeContext(domain="medicine", edge_type="CAUSES")
    system, user = get_rationale_prompts(
        a_name="Exercise",
        b_name="Cognitive Function",
        context=context,
        use_advanced=True
    )

    # Should include medicine or causal inference concepts
    assert any(keyword in system.lower() for keyword in ["medicine", "causal", "mechanism", "confounder"])


@pytest.mark.unit
def test_edge_rationale_different_edge_types():
    """Test that different edge types get different prompts."""
    from app.prompts.edge_rationale import get_rationale_prompts, EdgeContext

    context_causes = EdgeContext(edge_type="CAUSES")
    context_moderates = EdgeContext(edge_type="MODERATES")

    system_causes, _ = get_rationale_prompts("A", "B", context=context_causes, use_advanced=True)
    system_moderates, _ = get_rationale_prompts("A", "B", context=context_moderates, use_advanced=True)

    # Different edge types should have some different content
    assert system_causes != system_moderates


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
