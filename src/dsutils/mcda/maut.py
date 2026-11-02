"""Multi-attribute utility theory (MAUT) aggregation over a criteria hierarchy."""

import math
from collections import defaultdict
from collections.abc import Hashable
from typing import TypeAlias

import pandas as pd

Weights: TypeAlias = dict[str, dict[Hashable, float]]

WEIGHT_SUFFIX = " Weight"
GLOBAL_WEIGHT = "Global Weight"
WEIGHTED_SCORE = "Weighted Score"
SCORE = "Score"
RANK = "Rank"

_TOLERANCE = 1e-6
_MAX_REPORTED = 5


def run_maut(
    df: pd.DataFrame,
    levels: list[str],
    value: str,
    weights: Weights | None = None,
    alternatives: str | list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Score alternatives with an additive MAUT over a hierarchy of criteria.

    Each row of ``df`` is a leaf of the hierarchy: one alternative scored on one
    path of ``levels``. At every level, the children of a parent node receive
    local weights that sum to 1. The global weight of a leaf is the product of
    the local weights along its path, and an alternative's score is the sum of
    ``global weight * value`` over its leaves. Scores at any intermediate level
    can be recovered by grouping the returned detail and summing
    ``Weighted Score``.

    Weights default to ``1 / n`` among the children of each parent, where ``n``
    is the number of children present under that parent. Explicit weights in
    ``weights`` override the default as follows:

    - Keys are labels of the level, e.g. ``{"Impact Area": {"Economic": 0.4}}``.
      A plain label applies wherever that label occurs in the level.
    - A tuple key is a path ending at the label, e.g. ``("Social", "Other")``,
      matched against the trailing labels of ``levels``. The longest matching
      key wins, so tuples disambiguate labels that repeat under different
      parents. Tuples are always read as paths, never as labels.
    - Children without an explicit weight share the weight left over by their
      explicitly weighted siblings equally.

    Explicit weights also define which children a parent must have. Parents
    that share an explicitly weighted child form a sibling group, and every
    parent in a group must contain every explicitly weighted child of that
    group. This catches, for example, a measure that has no ``Costs`` rows when
    ``Costs`` carries an explicit impact weight. Complete such gaps in the data
    (e.g. with a fill value) before calling this function.

    Args:
        df: Long-format data with one row per alternative and leaf criterion.
            It is not modified.
        levels: Columns forming the criteria hierarchy, ordered from the top
            level to the leaf level. Every level is weighted.
        value: Numeric column holding the leaf-level utility of each row. Values
            should already be on a common scale and oriented so that higher is
            better.
        weights: Explicit local weights per level, as
            ``{level: {label_or_path: weight}}``. Levels that are omitted use
            equal weights.
        alternatives: Column or columns identifying what is being scored and
            ranked. These are never weighted. When ``None``, the whole of ``df``
            is scored as a single alternative.

    Returns:
        A tuple ``(detail, scores)``. ``detail`` is a copy of ``df`` with a
        ``"<level> Weight"`` column holding the local weight of each level,
        plus ``Global Weight`` and ``Weighted Score``. ``scores`` holds one row
        per alternative with its ``Score`` and ``Rank`` (1 is best, ties share
        the lowest rank), sorted by rank.

    Raises:
        KeyError: If ``levels``, ``value`` or ``alternatives`` name columns that
            are not in ``df``.
        TypeError: If ``value`` is not numeric.
        ValueError: If the inputs are inconsistent: ``df`` is empty, a column is
            used twice, identifying columns or ``value`` contain missing
            values, leaves are duplicated, output columns already exist,
            weights are negative, non-finite, unused or point to unknown
            levels, a parent lacks an explicitly weighted child of its sibling
            group, or a parent's local weights cannot sum to 1.
    """
    alternatives = (
        [alternatives] if isinstance(alternatives, str) else list(alternatives or [])
    )
    weights = weights or {}
    _validate_inputs(df, levels, value, weights, alternatives)

    detail = df.copy()
    weight_columns = [f"{level}{WEIGHT_SUFFIX}" for level in levels]
    for depth, column in enumerate(weight_columns):
        path = levels[: depth + 1]
        local = _local_weights(detail, alternatives, path, weights.get(path[-1], {}))
        detail = detail.join(local.rename(column), on=alternatives + path)

    detail[GLOBAL_WEIGHT] = detail[weight_columns].prod(axis=1)
    detail[WEIGHTED_SCORE] = detail[GLOBAL_WEIGHT] * detail[value]

    if alternatives:
        scores = detail.groupby(alternatives, as_index=False, sort=False)[
            WEIGHTED_SCORE
        ].sum()
        scores = scores.rename(columns={WEIGHTED_SCORE: SCORE})
    else:
        scores = pd.DataFrame({SCORE: [detail[WEIGHTED_SCORE].sum()]})
    scores[RANK] = scores[SCORE].rank(ascending=False, method="min").astype(int)
    scores = scores.sort_values(RANK, kind="stable").reset_index(drop=True)

    return detail, scores


def _validate_inputs(
    df: pd.DataFrame,
    levels: list[str],
    value: str,
    weights: Weights,
    alternatives: list[str],
) -> None:
    """Check that the inputs of `run_maut` are consistent with each other.

    Args:
        df: The data passed to `run_maut`.
        levels: The hierarchy columns, top to bottom.
        value: The numeric value column.
        weights: The explicit weights per level.
        alternatives: The alternative columns, already normalised to a list.

    Raises:
        KeyError: If a referenced column is not in ``df``.
        TypeError: If ``value`` is not numeric.
        ValueError: If any other consistency check fails.
    """
    if df.empty:
        raise ValueError("df is empty")
    if not levels:
        raise ValueError("levels must name at least one column")

    identifiers = alternatives + levels
    used = identifiers + [value]
    if len(set(used)) != len(used):
        raise ValueError(
            "Columns may only be used once across alternatives, levels and value: "
            f"{used}"
        )

    missing = [column for column in used if column not in df.columns]
    if missing:
        raise KeyError(f"Columns not found in df: {missing}")

    if not pd.api.types.is_numeric_dtype(df[value]):
        raise TypeError(f"Column {value!r} must be numeric, got {df[value].dtype}")

    null_columns = [column for column in used if df[column].isna().any()]
    if null_columns:
        raise ValueError(f"Columns contain missing values: {null_columns}")

    duplicates = df[df.duplicated(identifiers, keep=False)]
    if not duplicates.empty:
        raise ValueError(
            "Each alternative must have at most one row per leaf; aggregate "
            "duplicates first. Duplicated leaves:\n"
            f"{duplicates[identifiers].drop_duplicates().head(_MAX_REPORTED)}"
        )

    outputs = [f"{level}{WEIGHT_SUFFIX}" for level in levels] + [
        GLOBAL_WEIGHT,
        WEIGHTED_SCORE,
    ]
    clashes = [column for column in outputs if column in df.columns]
    clashes += [column for column in (SCORE, RANK) if column in alternatives]
    if clashes:
        raise ValueError(f"Output columns would overwrite existing columns: {clashes}")

    unknown_levels = [level for level in weights if level not in levels]
    if unknown_levels:
        raise ValueError(f"Weights given for levels not in levels: {unknown_levels}")

    for level, level_weights in weights.items():
        depth = levels.index(level) + 1
        for key, weight in level_weights.items():
            if isinstance(key, tuple) and not 1 <= len(key) <= depth:
                raise ValueError(
                    f"Weight key {key!r} for level {level!r} must be a path of 1 to "
                    f"{depth} labels"
                )
            if isinstance(weight, bool) or not isinstance(weight, int | float):
                raise ValueError(
                    f"Weight for {key!r} in level {level!r} must be a number, "
                    f"got {weight!r}"
                )
            if not math.isfinite(weight) or weight < 0:
                raise ValueError(
                    f"Weight for {key!r} in level {level!r} must be finite and >= 0, "
                    f"got {weight}"
                )


def _local_weights(
    df: pd.DataFrame,
    alternatives: list[str],
    path: list[str],
    level_weights: dict[Hashable, float],
) -> pd.Series:
    """Compute the local weight of every node at the deepest level of `path`.

    Args:
        df: The data being scored.
        alternatives: The alternative columns.
        path: The hierarchy columns from the top level down to the level being
            weighted.
        level_weights: Explicit weights for the level being weighted.

    Returns:
        Local weights indexed by the node's ``alternatives + path`` values.

    Raises:
        ValueError: If an explicit weight matches no node, a parent lacks an
            explicitly weighted child of its sibling group, or a parent's local
            weights cannot sum to 1.
    """
    level = path[-1]
    parent_columns = alternatives + path[:-1]
    nodes = df[alternatives + path].drop_duplicates().reset_index(drop=True)
    parents = _row_tuples(nodes[parent_columns])
    lookup = {_as_path(key): weight for key, weight in level_weights.items()}
    matched = [_match(node_path, lookup) for node_path in _row_tuples(nodes[path])]

    unused = [key for key in lookup if key not in set(matched)]
    if unused:
        raise ValueError(f"Weights for level {level!r} match no rows: {unused}")

    identities = [
        key if key is not None else (label,)
        for key, label in zip(matched, nodes[level])
    ]
    children = defaultdict(set)
    for parent, identity in zip(parents, identities):
        children[parent].add(identity)

    group_of = _sibling_groups(parents, matched)
    required = defaultdict(set)
    for parent, key in zip(parents, matched):
        if key is not None:
            required[group_of[parent]].add(key)

    errors = []
    for parent, present in children.items():
        absent = required[group_of[parent]] - present
        if absent:
            errors.append(
                f"{_describe(parent_columns, parent)} is missing "
                f"{sorted(absent, key=str)}"
            )
    _raise_if_any(errors, f"Missing explicitly weighted children at level {level!r}")

    explicit_total = defaultdict(float)
    unweighted_count = defaultdict(int)
    for parent, key in zip(parents, matched):
        if key is None:
            unweighted_count[parent] += 1
        else:
            explicit_total[parent] += lookup[key]

    for parent in children:
        residual = 1 - explicit_total[parent]
        if unweighted_count[parent] == 0 and abs(residual) > _TOLERANCE:
            errors.append(
                f"{_describe(parent_columns, parent)} has weights summing to "
                f"{1 - residual:g}"
            )
        elif unweighted_count[parent] > 0 and residual <= _TOLERANCE:
            errors.append(
                f"{_describe(parent_columns, parent)} leaves {residual:g} for "
                f"{unweighted_count[parent]} unweighted children; weight them "
                "explicitly"
            )
    _raise_if_any(errors, f"Local weights at level {level!r} do not sum to 1")

    local = [
        lookup[key]
        if key is not None
        else (1 - explicit_total[parent]) / unweighted_count[parent]
        for parent, key in zip(parents, matched)
    ]
    return pd.Series(local, index=_node_index(nodes))


def _node_index(nodes: pd.DataFrame) -> pd.Index:
    """Build an index from node columns that ``DataFrame.join`` can match on.

    Args:
        nodes: One column per identifying column of a node.

    Returns:
        A plain index for a single column, otherwise a ``MultiIndex``.
    """
    if nodes.shape[1] == 1:
        return pd.Index(nodes.iloc[:, 0])
    return pd.MultiIndex.from_frame(nodes)


def _row_tuples(frame: pd.DataFrame) -> list[tuple]:
    """Convert each row of `frame` to a tuple, including frames with no columns.

    Args:
        frame: The frame to convert.

    Returns:
        One tuple per row, empty tuples when ``frame`` has no columns.
    """
    if frame.shape[1] == 0:
        return [()] * len(frame)
    return list(frame.itertuples(index=False, name=None))


def _as_path(key: Hashable) -> tuple:
    """Normalise a weight key to a path of labels.

    Args:
        key: A label or a tuple path of labels.

    Returns:
        ``key`` itself when it is a tuple, otherwise a one-label path.
    """
    return key if isinstance(key, tuple) else (key,)


def _match(node_path: tuple, lookup: dict[tuple, float]) -> tuple | None:
    """Find the most specific weight key matching the end of `node_path`.

    Args:
        node_path: The labels of a node from the top level down.
        lookup: Explicit weights keyed by path.

    Returns:
        The longest key that equals a trailing slice of ``node_path``, or
        ``None`` when no key matches.
    """
    for length in range(len(node_path), 0, -1):
        candidate = node_path[-length:]
        if candidate in lookup:
            return candidate
    return None


def _sibling_groups(
    parents: list[tuple], matched: list[tuple | None]
) -> dict[tuple, tuple]:
    """Group parents that share at least one explicitly weighted child.

    Args:
        parents: The parent of each node.
        matched: The explicit weight key of each node, or ``None``.

    Returns:
        A mapping from each parent to a representative parent of its group.
    """
    root = {parent: parent for parent in parents}

    def find(parent: tuple) -> tuple:
        while root[parent] != parent:
            root[parent] = root[root[parent]]
            parent = root[parent]
        return parent

    first_parent = {}
    for parent, key in zip(parents, matched):
        if key is None:
            continue
        if key in first_parent:
            root[find(parent)] = find(first_parent[key])
        else:
            first_parent[key] = parent

    return {parent: find(parent) for parent in root}


def _describe(columns: list[str], parent: tuple) -> str:
    """Format a parent node for error messages.

    Args:
        columns: The columns identifying the parent.
        parent: The parent's values in ``columns``.

    Returns:
        A readable description of the parent.
    """
    if not columns:
        return "The top level"
    return ", ".join(f"{column}={label!r}" for column, label in zip(columns, parent))


def _raise_if_any(errors: list[str], message: str) -> None:
    """Raise a single error summarising `errors`, if there are any.

    Args:
        errors: Individual problems found.
        message: Summary line of the error.

    Raises:
        ValueError: If ``errors`` is not empty.
    """
    if not errors:
        return
    shown = "\n".join(f"  - {error}" for error in errors[:_MAX_REPORTED])
    more = (
        f"\n  ... and {len(errors) - _MAX_REPORTED} more"
        if len(errors) > _MAX_REPORTED
        else ""
    )
    raise ValueError(f"{message}:\n{shown}{more}")
