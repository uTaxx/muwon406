import jsonschema
import pytest

from keyword_groups import active_keyword_groups, load_keyword_groups


def test_load_local_yaml_groups_pass_schema_validation():
    groups = load_keyword_groups()
    assert len(groups) >= 1
    assert groups[0]["group_id"] == "GRP-0001"
    assert groups[0]["topic_id"] == "TOP-0001"


def test_active_keyword_groups_filters_disabled(monkeypatch):
    groups = [
        {
            "group_id": "GRP-0001", "topic_id": "TOP-0001", "group_name": "A",
            "include_keywords": ["x"], "exclude_keywords": [], "ai_instructions": "",
            "sources": ["SRC-0001"], "enabled": True,
        },
        {
            "group_id": "GRP-0002", "topic_id": "TOP-0001", "group_name": "B",
            "include_keywords": ["y"], "exclude_keywords": [], "ai_instructions": "",
            "sources": ["SRC-0001"], "enabled": False,
        },
    ]
    result = active_keyword_groups(groups)
    assert [g["group_id"] for g in result] == ["GRP-0001"]


def test_unknown_source_raises_value_error():
    with pytest.raises(ValueError):
        load_keyword_groups(source="not_a_real_source")


def test_group_missing_required_field_fails_schema(monkeypatch):
    import keyword_groups as kg

    bad_group = {
        "group_id": "GRP-0001", "topic_id": "TOP-0001", "group_name": "A",
        "include_keywords": ["x"], "exclude_keywords": [], "ai_instructions": "",
        "sources": ["SRC-0001"],
        # enabled 누락
    }
    monkeypatch.setattr(kg, "load_yaml", lambda path: {"keyword_groups": [bad_group]})
    with pytest.raises(jsonschema.ValidationError):
        kg.load_keyword_groups()


def test_google_sheets_mode_parses_csv_and_boolean_strings(monkeypatch):
    import keyword_groups as kg

    class _FakeSheetsStorage:
        def __init__(self, **kwargs):
            pass

        def load_all(self, collection):
            assert collection == "KEYWORD_GROUPS"
            return [
                {
                    "group_id": "GRP-0001",
                    "topic_id": "TOP-0001",
                    "group_name": "실리코시스",
                    "include_keywords": "silicosis, engineered stone",
                    "exclude_keywords": "sports",
                    "ai_instructions": "LX하우시스 관점",
                    "sources": "SRC-0001,SRC-0002",
                    "enabled": "TRUE",
                }
            ]

    monkeypatch.setattr("storage.google_sheets_storage.GoogleSheetsStorage", _FakeSheetsStorage)
    groups = kg.load_keyword_groups(source="google_sheets", spreadsheet_id="fake-id")
    assert groups[0]["include_keywords"] == ["silicosis", "engineered stone"]
    assert groups[0]["sources"] == ["SRC-0001", "SRC-0002"]
    assert groups[0]["enabled"] is True
