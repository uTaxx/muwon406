import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"
FIXTURES_DIR = ROOT / "tests" / "fixtures"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _schema(name: str):
    return _load_json(SCHEMAS_DIR / name)


@pytest.mark.parametrize("schema_file", [
    "article.schema.json",
    "intelligence.schema.json",
    "source_health.schema.json",
    "change_request.schema.json",
    "claude_output.schema.json",
])
def test_schema_files_are_valid_json_schema(schema_file):
    schema = _schema(schema_file)
    jsonschema.Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("fixture_file", [
    "article_valid.json",
    "article_valid_null_amounts.json",
])
def test_valid_article_fixtures_pass(fixture_file):
    schema = _schema("article.schema.json")
    data = _load_json(FIXTURES_DIR / fixture_file)
    jsonschema.validate(instance=data, schema=schema)


def test_invalid_article_fixture_fails():
    schema = _schema("article.schema.json")
    data = _load_json(FIXTURES_DIR / "article_invalid_missing_required.json")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=data, schema=schema)


def test_average_amount_per_person_can_be_null():
    data = _load_json(FIXTURES_DIR / "article_valid_null_amounts.json")
    assert data["average_amount_per_person_usd"] is None
    assert data["litigation_amount_total_usd"] is None
    assert data["claimant_count"] is None


def test_valid_intelligence_fixture_passes():
    schema = _schema("intelligence.schema.json")
    data = _load_json(FIXTURES_DIR / "intelligence_valid.json")
    jsonschema.validate(instance=data, schema=schema)


def test_invalid_intelligence_fixture_fails_empty_evidence():
    schema = _schema("intelligence.schema.json")
    data = _load_json(FIXTURES_DIR / "intelligence_invalid_missing_evidence.json")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=data, schema=schema)


def test_valid_source_health_fixture_passes():
    schema = _schema("source_health.schema.json")
    data = _load_json(FIXTURES_DIR / "source_health_valid.json")
    jsonschema.validate(instance=data, schema=schema)


def test_invalid_source_health_fixture_fails():
    schema = _schema("source_health.schema.json")
    data = _load_json(FIXTURES_DIR / "source_health_invalid_bad_status.json")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=data, schema=schema)


def test_claude_relevance_output_example_validates():
    schema = _schema("claude_output.schema.json")
    example = {
        "relevant": True,
        "relevance_score": 0.9,
        "mission": "risk_management",
        "related_companies": ["LX Hausys"],
        "reason": "샘플 근거",
        "needs_deep_analysis": True,
    }
    jsonschema.validate(instance=example, schema=schema)


def test_claude_risk_analysis_output_example_validates():
    schema = _schema("claude_output.schema.json")
    example = {
        "facts": ["샘플 사실"],
        "significance": "high",
        "lx_impact": [],
        "actions": [],
        "confidence": "medium",
        "evidence": ["https://example.com/a"],
        "unknowns": [],
    }
    jsonschema.validate(instance=example, schema=schema)


def test_google_sheets_columns_json_is_well_formed():
    data = _load_json(SCHEMAS_DIR / "google_sheets_columns.json")
    assert len(data["sheets"]) == 11
    for name, entry in data["sheets"].items():
        assert entry["status"] in ("confirmed", "draft")
        assert isinstance(entry["columns"], list) and entry["columns"]
