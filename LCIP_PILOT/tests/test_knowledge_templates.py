import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"

# Architect Review Round 3 Q5: 회사 프로필류 Knowledge 문서는 전부 동일한 16계층
# Taxonomy(1~12 + Source/Reference URL/Confidence/Last Verified)를 따라야 한다.
COMPANY_PROFILE_DOCS = ["LX_HAUSYS_COMPANY_DNA.md", "LX_HOLDINGS_CONTEXT.md"]

EXPECTED_LAYER_NAMES = [
    "Company", "Business", "Product", "Manufacturing", "Value Chain", "Customer",
    "Competitor", "Raw Material", "Government", "Risk", "Opportunity", "Investment Point",
]


def _section_headers(text: str) -> list[str]:
    return re.findall(r"^## (\d+)\. ([^—\n]+)", text, flags=re.MULTILINE)


def test_company_profile_docs_share_the_same_16_layer_template():
    for filename in COMPANY_PROFILE_DOCS:
        text = (KNOWLEDGE_DIR / filename).read_text(encoding="utf-8")
        headers = _section_headers(text)
        numbered = [(int(n), name.strip()) for n, name in headers if n.isdigit() and int(n) <= 12]
        assert len(numbered) == 12, f"{filename}: 12개 계층이 아님 ({len(numbered)}개 발견)"
        for (num, name), expected in zip(numbered, EXPECTED_LAYER_NAMES):
            assert name.startswith(expected), f"{filename} 계층 {num}: '{name}' != '{expected}'"


def test_holdings_context_marks_non_applicable_layers_as_na():
    text = (KNOWLEDGE_DIR / "LX_HOLDINGS_CONTEXT.md").read_text(encoding="utf-8")
    for layer in ["Product", "Manufacturing", "Value Chain", "Customer", "Competitor", "Raw Material"]:
        assert f"— N/A" in text or "N/A" in text
    assert text.count("Not Applicable") >= 6


def test_company_profile_docs_have_source_metadata_per_section():
    for filename in COMPANY_PROFILE_DOCS:
        text = (KNOWLEDGE_DIR / filename).read_text(encoding="utf-8")
        assert text.count("Source:") >= 12
