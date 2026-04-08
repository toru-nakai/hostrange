"""Tests for hostrange expansion."""

import pytest

from hostrange import expand


class TestBasicRanges:
    def test_numeric_range(self):
        assert expand("n[1-5]") == ["n1", "n2", "n3", "n4", "n5"]

    def test_zero_padded_range(self):
        assert expand("c[01-05]") == ["c01", "c02", "c03", "c04", "c05"]

    def test_zero_padded_wider(self):
        assert expand("n[001-003]") == ["n001", "n002", "n003"]

    def test_no_padding_crossing_digits(self):
        assert expand("n[8-12]") == ["n8", "n9", "n10", "n11", "n12"]

    def test_zero_padded_crossing_digits(self):
        assert expand("n[08-12]") == ["n08", "n09", "n10", "n11", "n12"]


class TestCommaInBrackets:
    def test_comma_separated_values(self):
        assert expand("n[1,3,5]") == ["n1", "n3", "n5"]

    def test_mixed_range_and_values(self):
        assert expand("n[1-3,5-7]") == ["n1", "n2", "n3", "n5", "n6", "n7"]

    def test_mixed_with_single(self):
        assert expand("n[1-3,5]") == ["n1", "n2", "n3", "n5"]


class TestTopLevelComma:
    def test_two_groups(self):
        assert expand("n[1-3],c[01-03]") == ["n1", "n2", "n3", "c01", "c02", "c03"]

    def test_three_groups(self):
        result = expand("a[1-2],b[1-2],c[1-2]")
        assert result == ["a1", "a2", "b1", "b2", "c1", "c2"]


class TestNoPattern:
    def test_plain_hostname(self):
        assert expand("n1") == ["n1"]

    def test_empty_string(self):
        assert expand("") == []


class TestPrefix:
    def test_long_prefix(self):
        assert expand("server[1-3]") == ["server1", "server2", "server3"]

    def test_no_prefix(self):
        assert expand("[1-3]") == ["1", "2", "3"]

    def test_suffix(self):
        assert expand("n[1-3].example.com") == [
            "n1.example.com",
            "n2.example.com",
            "n3.example.com",
        ]


class TestMultipleBrackets:
    def test_two_brackets(self):
        result = expand("rack[1-2]-node[01-02]")
        assert result == [
            "rack1-node01",
            "rack1-node02",
            "rack2-node01",
            "rack2-node02",
        ]


class TestListInput:
    def test_list_of_patterns(self):
        assert expand(["n[1-2]", "c[01-02]"]) == ["n1", "n2", "c01", "c02"]


class TestInvalidPatterns:
    def test_unclosed_bracket(self):
        with pytest.raises(ValueError, match="Unmatched brackets"):
            expand("n[1-5")

    def test_extra_closing_bracket(self):
        with pytest.raises(ValueError, match="Unmatched brackets"):
            expand("n1-5]")

    def test_empty_brackets(self):
        with pytest.raises(ValueError, match="Empty brackets"):
            expand("n[]")

    def test_nested_brackets(self):
        with pytest.raises(ValueError, match="Nested brackets"):
            expand("n[[1-5]]")

    def test_non_numeric_range_end(self):
        with pytest.raises(ValueError):
            expand("n[1-z]")

    def test_non_numeric_range_start(self):
        with pytest.raises(ValueError):
            expand("n[a-5]")
    
    def test_empty_list(self):
        assert expand('') == []
    
    def test_non_string_input(self):
        with pytest.raises(TypeError):
            expand(123)
