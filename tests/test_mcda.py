import pandas as pd
import pytest

from dsutils.mcda.maut import run_maut

LEVELS = ["Measure", "Impact", "Sub"]


@pytest.fixture
def data():
    rows = [
        ("A", "M1", "Econ", "e1", 1.0),
        ("A", "M1", "Econ", "e2", 3.0),
        ("A", "M1", "Social", "s1", 2.0),
        ("A", "M2", "Econ", "e1", 0.0),
        ("A", "M2", "Econ", "e2", 2.0),
        ("A", "M2", "Social", "s1", 4.0),
        ("B", "M3", "Econ", "e1", 2.0),
        ("B", "M3", "Econ", "e2", 2.0),
        ("B", "M3", "Social", "s1", 1.0),
    ]
    columns = ["Option", *LEVELS, "Value"]
    return pd.DataFrame(rows, columns=columns, index=range(10, 19))


def scores_by_option(scores):
    return dict(zip(scores["Option"], scores["Score"]))


def test_equal_weights_by_default(data):
    detail, scores = run_maut(data, LEVELS, "Value", alternatives="Option")

    assert scores_by_option(scores) == pytest.approx({"A": 2.25, "B": 1.5})
    assert scores["Rank"].tolist() == [1, 2]
    assert detail.groupby("Option")["Global Weight"].sum().tolist() == pytest.approx([
        1,
        1,
    ])


def test_explicit_weights_and_ties(data):
    weights = {"Impact": {"Econ": 0.8, "Social": 0.2}}
    _, scores = run_maut(data, LEVELS, "Value", weights, alternatives="Option")

    assert scores_by_option(scores) == pytest.approx({"A": 1.8, "B": 1.8})
    assert scores["Rank"].tolist() == [1, 1]


def test_partial_weights_share_the_residual(data):
    detail, _ = run_maut(
        data, LEVELS, "Value", {"Sub": {"e1": 0.7}}, alternatives="Option"
    )

    sub_weights = detail.groupby("Sub")["Sub Weight"].unique()
    assert sub_weights["e1"] == pytest.approx([0.7])
    assert sub_weights["e2"] == pytest.approx([0.3])
    assert sub_weights["s1"] == pytest.approx([1.0])


def test_tuple_keys_disambiguate_repeated_labels():
    df = pd.DataFrame({
        "Impact": ["Econ", "Econ", "Social", "Social"],
        "Sub": ["e1", "Other", "s1", "Other"],
        "Value": [1.0, 1.0, 1.0, 1.0],
    })
    weights = {"Sub": {"Other": 0.1, ("Social", "Other"): 0.6}}
    detail, _ = run_maut(df, ["Impact", "Sub"], "Value", weights)

    assert detail["Sub Weight"].tolist() == pytest.approx([0.9, 0.1, 0.4, 0.6])


def test_without_alternatives_scores_one_row(data):
    _, scores = run_maut(data[data["Option"] == "B"], LEVELS, "Value")

    assert scores["Score"].tolist() == pytest.approx([1.5])
    assert scores["Rank"].tolist() == [1]


def test_input_is_not_modified_and_index_is_kept(data):
    original = data.copy()
    detail, _ = run_maut(data, LEVELS, "Value", alternatives="Option")

    pd.testing.assert_frame_equal(data, original)
    assert detail.index.equals(data.index)


def test_unbalanced_hierarchy_is_allowed_with_equal_weights(data):
    data = data.drop(index=18)
    _, scores = run_maut(data, LEVELS, "Value", alternatives="Option")

    assert scores_by_option(scores)["B"] == pytest.approx(2.0)


def test_missing_explicitly_weighted_child_raises(data):
    data = data.drop(index=18)
    weights = {"Impact": {"Econ": 0.8, "Social": 0.2}}

    with pytest.raises(ValueError, match="Measure='M3' is missing"):
        run_maut(data, LEVELS, "Value", weights, alternatives="Option")


@pytest.mark.parametrize(
    "weights, message",
    [
        ({"Impact": {"Econ": 0.5, "Social": 0.4}}, "summing to 0.9"),
        ({"Impact": {"Econ": 1.0}}, "weight them explicitly"),
        ({"Impact": {"Econmic": 1.0}}, "match no rows"),
        ({"Region": {"EU": 1.0}}, "levels not in levels"),
        ({"Impact": {"Econ": -0.1}}, "finite and >= 0"),
        ({"Impact": {("M1", "Econ", "x"): 0.5}}, "path of 1 to 2 labels"),
    ],
)
def test_invalid_weights_raise(data, weights, message):
    with pytest.raises(ValueError, match=message):
        run_maut(data, LEVELS, "Value", weights, alternatives="Option")


def test_duplicate_leaves_raise(data):
    with pytest.raises(ValueError, match="at most one row per leaf"):
        run_maut(
            pd.concat([data, data.head(1)]), LEVELS, "Value", alternatives="Option"
        )


def test_missing_columns_raise(data):
    with pytest.raises(KeyError, match="Region"):
        run_maut(data, ["Region", *LEVELS], "Value", alternatives="Option")
