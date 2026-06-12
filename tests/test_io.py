from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from dsutils.io.json import load_json, save_json


@pytest.mark.parametrize(
    "sample_data, fake_file_content",
    [
        ({"key": "value"}, '{"key": "value"}'),
        (["item_1", 2, True], '["item_1", 2, True]'),
        ("just a string", '"just a string"'),
        (42, "42"),
        (3.14, "3.14"),
        (True, "true"),
        (None, "null"),
    ],
)
@patch("dsutils.io.json.json")
def test_load_json_all_types(mock_json, sample_data, fake_file_content):
    sample_path = Path("example.json")
    mock_json.load.return_value = sample_data
    m_open = mock_open(read_data=fake_file_content)

    with patch("dsutils.io.json.open", m_open):
        result = load_json(sample_path)

    assert result == sample_data
    m_open.assert_called_once_with(sample_path)
    mock_json.load.assert_called_once()


@pytest.mark.parametrize(
    "sample_data",
    [
        {"key": "value"},
        (["item_1", 2, True]),
        ("just a string"),
        (42),
        (3.14),
        (True),
        (None),
    ],
)
@patch("dsutils.io.json.json")
def test_save_json_all_types(mock_json, sample_data):
    sample_path = Path("output.json")
    m_open = mock_open()

    with patch("dsutils.io.json.open", m_open):
        save_json(sample_path, sample_data, indent=2)

    m_open.assert_called_once_with(sample_path, "w")
    mock_json.dump.assert_called_once_with(sample_data, m_open(), indent=2)
