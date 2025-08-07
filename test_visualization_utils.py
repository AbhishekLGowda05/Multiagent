import pytest

from visualization_utils import generate_chart


def test_generate_chart_empty_data(tmp_path):
    with pytest.raises(ValueError, match="cannot be empty"):
        generate_chart(data=[], labels=[], path=str(tmp_path / "empty.png"))


def test_generate_chart_mismatched_labels(tmp_path):
    with pytest.raises(ValueError, match="same length"):
        generate_chart(data=[1, 2], labels=["one"], path=str(tmp_path / "mismatch.png"))
