"""
Unit tests for k1_parser module.

Tests regex-based extraction of K-1 form fields from OCR/native text.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from k1_extractor.k1_parser import (
    parse_k1,
    parse_k1_multi,
    clean_currency,
    _detect_form_type,
    _extract_entity_info,
    _extract_recipient_info,
    _extract_boxes,
    _split_k1_sections,
)


class TestCleanCurrency(unittest.TestCase):
    """Test the clean_currency helper function."""

    def test_basic_amount(self):
        self.assertEqual(clean_currency("1234"), "1234")

    def test_with_dollar_sign(self):
        self.assertEqual(clean_currency("$1,234.56"), "1234.56")

    def test_negative_parentheses(self):
        self.assertEqual(clean_currency("(1,234.56)"), "-1234.56")

    def test_negative_dash(self):
        self.assertEqual(clean_currency("-1,234"), "-1234")

    def test_with_commas(self):
        self.assertEqual(clean_currency("1,234,567"), "1234567")

    def test_zero_returns_empty(self):
        self.assertEqual(clean_currency("0"), "")
        self.assertEqual(clean_currency("$0.00"), "")

    def test_empty_returns_empty(self):
        self.assertEqual(clean_currency(""), "")

    def test_non_numeric_returns_empty(self):
        self.assertEqual(clean_currency("abc"), "")

    def test_with_spaces(self):
        self.assertEqual(clean_currency("$ 1,234.56"), "1234.56")

    def test_integer_no_decimals(self):
        self.assertEqual(clean_currency("5000.00"), "5000")

    def test_decimal_value(self):
        self.assertEqual(clean_currency("123.45"), "123.45")

    def test_ocr_s_for_dollar(self):
        self.assertEqual(clean_currency("S1234"), "1234")


class TestDetectFormType(unittest.TestCase):
    """Test form type detection from text."""

    def test_detect_1065(self):
        text = "Schedule K-1 (Form 1065) Partner's Share of Income"
        self.assertEqual(_detect_form_type(text), "1065")

    def test_detect_1120s(self):
        text = "Schedule K-1 (Form 1120-S) Shareholder's Share of Income"
        self.assertEqual(_detect_form_type(text), "1120S")

    def test_detect_1041(self):
        text = "Schedule K-1 (Form 1041) Beneficiary's Share of Income"
        self.assertEqual(_detect_form_type(text), "1041")

    def test_detect_by_keywords_partner(self):
        text = "The partnership reported the following for the partner"
        self.assertEqual(_detect_form_type(text), "1065")

    def test_detect_by_keywords_shareholder(self):
        text = "S corporation shareholder share of income"
        self.assertEqual(_detect_form_type(text), "1120S")

    def test_detect_by_keywords_beneficiary(self):
        text = "Estate trust beneficiary income distribution fiduciary"
        self.assertEqual(_detect_form_type(text), "1041")

    def test_default_to_1065(self):
        text = "Some random text with no form indicators"
        self.assertEqual(_detect_form_type(text), "1065")


class TestExtractEntityInfo(unittest.TestCase):
    """Test entity info extraction."""

    def test_extract_ein(self):
        text = "Partnership's EIN: 12-3456789\nPartnership's name: Test LLC"
        info = _extract_entity_info(text, "1065")
        self.assertEqual(info["ein"], "12-3456789")

    def test_extract_entity_name(self):
        text = "Partnership's name: ABC Partners LP\nAddress: 123 Main St"
        info = _extract_entity_info(text, "1065")
        self.assertEqual(info["name"], "ABC Partners LP")

    def test_extract_tax_year(self):
        text = "Tax year beginning 01/01/2024 ending 12/31/2024"
        info = _extract_entity_info(text, "1065")
        self.assertEqual(info["tax_year_begin"], "01/01/2024")
        self.assertEqual(info["tax_year_end"], "12/31/2024")

    def test_extract_calendar_year(self):
        text = "Calendar year 2024\nSchedule K-1"
        info = _extract_entity_info(text, "1065")
        self.assertEqual(info["tax_year_end"], "2024")


class TestExtractRecipientInfo(unittest.TestCase):
    """Test recipient info extraction."""

    def test_extract_ssn(self):
        text = "Partner's SSN: 123-45-6789\nPartner's name: John Smith"
        info = _extract_recipient_info(text, "1065")
        self.assertEqual(info["id"], "123-45-6789")

    def test_extract_partner_name(self):
        text = "Partner's name: Jane Doe\nAddress: 456 Oak Ave"
        info = _extract_recipient_info(text, "1065")
        self.assertEqual(info["name"], "Jane Doe")

    def test_general_partner_type(self):
        text = "General partner or LLC member-manager"
        info = _extract_recipient_info(text, "1065")
        self.assertEqual(info["type"], "General partner")

    def test_limited_partner_type(self):
        text = "Limited partner or other LLC member"
        info = _extract_recipient_info(text, "1065")
        self.assertEqual(info["type"], "Limited partner")

    def test_shareholder_type(self):
        info = _extract_recipient_info("Some text", "1120S")
        self.assertEqual(info["type"], "Shareholder")


class TestExtractBoxes(unittest.TestCase):
    """Test Part III box value extraction."""

    def test_extract_box_1(self):
        text = "1 Ordinary business income (loss) $25,000"
        boxes = _extract_boxes(text, "1065")
        self.assertEqual(boxes.get("1"), "25000")

    def test_extract_negative_box(self):
        text = "Box 1 Ordinary business income (loss) (5,000)"
        boxes = _extract_boxes(text, "1065")
        self.assertEqual(boxes.get("1"), "-5000")

    def test_extract_multiple_boxes(self):
        text = """
        1 Ordinary business income (loss) $10,000
        5 Interest income $500
        7 Royalties $1,200.50
        """
        boxes = _extract_boxes(text, "1065")
        self.assertEqual(boxes.get("1"), "10000")
        self.assertEqual(boxes.get("5"), "500")
        self.assertEqual(boxes.get("7"), "1200.50")

    def test_zero_value_excluded(self):
        text = "1 Ordinary business income (loss) $0"
        boxes = _extract_boxes(text, "1065")
        self.assertNotIn("1", boxes)


class TestParseK1Integration(unittest.TestCase):
    """Integration tests for the full parse_k1 function."""

    SAMPLE_1065_TEXT = """
    Schedule K-1 (Form 1065)
    Department of the Treasury
    Internal Revenue Service

    For calendar year 2024

    Part I Information About the Partnership
    Partnership's name: Acme Investment Partners LP
    Partnership's EIN: 98-7654321
    Tax year beginning 01/01/2024 ending 12/31/2024

    Part II Information About the Partner
    Partner's name: John Q. Taxpayer
    Partner's identifying number: 123-45-6789
    General partner or LLC member-manager

    Part III Partner's Share of Current Year Income
    1 Ordinary business income (loss) $45,000
    5 Interest income $1,250
    6a Ordinary dividends $3,500
    6b Qualified dividends $2,800
    7 Royalties $0
    8 Net short-term capital gain (loss) ($2,100)
    9a Net long-term capital gain (loss) $15,750
    14 Self-employment earnings (loss) $45,000
    19 Distributions $20,000
    """

    def test_full_1065_parse(self):
        result = parse_k1(self.SAMPLE_1065_TEXT, "test_k1.pdf", "native")

        self.assertEqual(result.form_type, "1065")
        self.assertEqual(result.source_file, "test_k1.pdf")
        self.assertEqual(result.extraction_method, "native")
        self.assertEqual(result.entity_name, "Acme Investment Partners LP")
        self.assertEqual(result.entity_ein, "98-7654321")
        self.assertEqual(result.recipient_name, "John Q. Taxpayer")
        self.assertEqual(result.recipient_id, "123-45-6789")
        self.assertEqual(result.recipient_type, "General partner")
        self.assertEqual(result.tax_year_begin, "01/01/2024")
        self.assertEqual(result.tax_year_end, "12/31/2024")

        # Check box values
        self.assertEqual(result.boxes.get("1"), "45000")
        self.assertEqual(result.boxes.get("5"), "1250")
        self.assertEqual(result.boxes.get("6a"), "3500")
        self.assertEqual(result.boxes.get("8"), "-2100")
        self.assertEqual(result.boxes.get("9a"), "15750")

        # Confidence should be high given all fields are present
        self.assertEqual(result.confidence, "high")

    SAMPLE_1120S_TEXT = """
    Schedule K-1 (Form 1120-S)
    Shareholder's Share of Income, Deductions, Credits, etc.

    For calendar year 2024

    Corporation's name: TechCorp Inc
    Corporation's EIN: 55-1234567

    Shareholder's name: Alice Johnson
    Shareholder's identifying number: 987-65-4321

    1 Ordinary business income (loss) $32,000
    4 Interest income $800
    5a Ordinary dividends $1,500
    7 Net short-term capital gain (loss) $0
    8a Net long-term capital gain (loss) $5,200
    """

    def test_full_1120s_parse(self):
        result = parse_k1(self.SAMPLE_1120S_TEXT, "scorp_k1.pdf", "native")

        self.assertEqual(result.form_type, "1120S")
        self.assertEqual(result.entity_ein, "55-1234567")
        self.assertEqual(result.recipient_id, "987-65-4321")
        self.assertEqual(result.recipient_type, "Shareholder")
        self.assertEqual(result.boxes.get("1"), "32000")
        self.assertEqual(result.boxes.get("4"), "800")
        self.assertEqual(result.boxes.get("8a"), "5200")

    SAMPLE_1041_TEXT = """
    Schedule K-1 (Form 1041)
    Beneficiary's Share of Income, Deductions, Credits, etc.

    For calendar year 2024

    Estate's name: Estate of Robert Smith
    Estate's EIN: 77-8889999

    Beneficiary's name: Mary Smith
    Beneficiary's identifying number: 111-22-3333

    1 Interest income $2,500
    2a Ordinary dividends $1,800
    2b Qualified dividends $1,200
    3 Net short-term capital gain $500
    """

    def test_full_1041_parse(self):
        result = parse_k1(self.SAMPLE_1041_TEXT, "trust_k1.pdf", "ocr")

        self.assertEqual(result.form_type, "1041")
        self.assertEqual(result.entity_ein, "77-8889999")
        self.assertEqual(result.recipient_id, "111-22-3333")
        self.assertEqual(result.recipient_type, "Beneficiary")
        self.assertEqual(result.extraction_method, "ocr")
        self.assertEqual(result.boxes.get("1"), "2500")
        self.assertEqual(result.boxes.get("2a"), "1800")
        self.assertEqual(result.boxes.get("2b"), "1200")


class TestK1DataModel(unittest.TestCase):
    """Test K1Data model methods."""

    def test_tax_year_display(self):
        from k1_extractor.models import K1Data
        k1 = K1Data(source_file="test.pdf", form_type="1065",
                     tax_year_begin="01/01/2024", tax_year_end="12/31/2024")
        self.assertEqual(k1.tax_year, "01/01/2024 - 12/31/2024")

    def test_box_value_as_float(self):
        from k1_extractor.models import K1Data
        k1 = K1Data(source_file="test.pdf", form_type="1065",
                     boxes={"1": "25000", "8": "-2100", "5": "1234.56"})
        self.assertEqual(k1.box_value_as_float("1"), 25000.0)
        self.assertEqual(k1.box_value_as_float("8"), -2100.0)
        self.assertEqual(k1.box_value_as_float("5"), 1234.56)
        self.assertIsNone(k1.box_value_as_float("99"))

    def test_box_value_as_float_parenthesized(self):
        from k1_extractor.models import K1Data
        k1 = K1Data(source_file="test.pdf", form_type="1065",
                     boxes={"1": "(5000)"})
        self.assertEqual(k1.box_value_as_float("1"), -5000.0)


class TestSplitK1Sections(unittest.TestCase):
    """Test splitting multi-K1 text into individual sections."""

    def test_single_form_returns_one_section(self):
        text = """
        Schedule K-1 (Form 1065)
        Partner's Share of Income
        Partnership's name: Test LP
        1 Ordinary business income $10,000
        """
        sections = _split_k1_sections(text)
        self.assertEqual(len(sections), 1)

    def test_two_forms_returns_two_sections(self):
        form1 = """
        Schedule K-1 (Form 1065)
        Partner's Share of Current Year Income
        Partnership's name: Test LP
        Partner's name: John Smith
        1 Ordinary business income $10,000
        """
        form2 = """
        Schedule K-1 (Form 1065)
        Partner's Share of Current Year Income
        Partnership's name: Test LP
        Partner's name: Jane Doe
        1 Ordinary business income $20,000
        """
        text = form1 + "\n" + form2
        sections = _split_k1_sections(text)
        self.assertEqual(len(sections), 2)
        self.assertIn("John Smith", sections[0])
        self.assertIn("Jane Doe", sections[1])

    def test_nearby_headers_not_split(self):
        text = """
        Schedule K-1 (Form 1065)
        Partner's Share of Current Year Income
        Partnership's name: Test LP
        1 Ordinary business income $10,000
        """
        sections = _split_k1_sections(text)
        # "Schedule K-1" and "Partner's Share" are close together = same form
        self.assertEqual(len(sections), 1)

    def test_three_forms(self):
        forms = []
        for name in ["Alice", "Bob", "Charlie"]:
            forms.append(f"""
            Schedule K-1 (Form 1065)
            Partner's Share of Current Year Income
            Partnership's name: Test LP
            Partner's name: {name}
            1 Ordinary business income $10,000
            """)
        text = "\n".join(forms)
        sections = _split_k1_sections(text)
        self.assertEqual(len(sections), 3)


class TestParseK1Multi(unittest.TestCase):
    """Test multi-K1 parsing from a single document."""

    def test_multi_k1_returns_multiple_results(self):
        form1 = """
        Schedule K-1 (Form 1065)
        Partner's Share of Current Year Income
        Partnership's name: Acme LP
        Partnership's EIN: 12-3456789
        For calendar year 2024
        Partner's name: John Smith
        Partner's identifying number: 111-22-3333
        General partner
        1 Ordinary business income (loss) $50,000
        5 Interest income $1,000
        """
        form2 = """
        Schedule K-1 (Form 1065)
        Partner's Share of Current Year Income
        Partnership's name: Acme LP
        Partnership's EIN: 12-3456789
        For calendar year 2024
        Partner's name: Jane Doe
        Partner's identifying number: 444-55-6666
        Limited partner
        1 Ordinary business income (loss) $25,000
        5 Interest income $500
        """
        text = form1 + "\n" + form2
        results = parse_k1_multi(text, "multi_k1.pdf", "native")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].source_file, "multi_k1.pdf [K-1 #1]")
        self.assertEqual(results[1].source_file, "multi_k1.pdf [K-1 #2]")
        self.assertEqual(results[0].recipient_name, "John Smith")
        self.assertEqual(results[1].recipient_name, "Jane Doe")
        self.assertEqual(results[0].boxes.get("1"), "50000")
        self.assertEqual(results[1].boxes.get("1"), "25000")

    def test_single_k1_returns_one_result(self):
        text = """
        Schedule K-1 (Form 1065)
        Partner's Share of Current Year Income
        Partnership's name: Solo LP
        Partner's name: Only Partner
        1 Ordinary business income (loss) $10,000
        """
        results = parse_k1_multi(text, "single.pdf", "native")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_file, "single.pdf")


if __name__ == "__main__":
    unittest.main()
