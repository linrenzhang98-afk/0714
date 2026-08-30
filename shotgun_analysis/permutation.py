"""Deterministic, optionally stratum-restricted permutation generation."""

from __future__ import annotations

import random
from collections import defaultdict
from collections import Counter
from typing import Hashable, Iterator, Sequence

from .errors import InputValidationError


def restricted_permutations(
    n_samples: int,
    n_permutations: int,
    seed: int,
    strata: Sequence[Hashable] | None = None,
) -> Iterator[list[int]]:
    """Return a deterministic streaming iterator of permutation index maps.

    Maps are sampled with replacement, as in a Monte Carlo permutation test.
    They are yielded one at a time so a 9,999-permutation production run does
    not retain all maps in memory.
    """
    if n_samples < 2 or n_permutations < 1:
        raise InputValidationError("permutations require at least two samples and one permutation")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise InputValidationError("seed must be an integer")
    if strata is not None and len(strata) != n_samples:
        raise InputValidationError("strata length does not match sample count")
    blocks: dict[Hashable, list[int]] = defaultdict(list)
    if strata is None:
        blocks["__all__"] = list(range(n_samples))
    else:
        for index, block in enumerate(strata):
            blocks[block].append(index)
    if all(len(indices) < 2 for indices in blocks.values()):
        raise InputValidationError("every permutation stratum is a singleton")
    frozen_blocks = [tuple(indices) for indices in blocks.values()]

    def iterator() -> Iterator[list[int]]:
        rng = random.Random(seed)
        for _ in range(n_permutations):
            permutation = list(range(n_samples))
            for indices in frozen_blocks:
                shuffled = list(indices)
                rng.shuffle(shuffled)
                for target, source in zip(indices, shuffled):
                    permutation[target] = source
            yield permutation

    return iterator()


def validate_block_exchangeability(
    groups: Sequence[str],
    strata: Sequence[Hashable],
    *,
    minimum_per_group_per_block: int = 2,
) -> dict[str, dict[str, int]]:
    """Fail closed when a blocked clinical-label permutation is not viable.

    The frozen anchor design requires every diagnosis in each Training/Test
    block with at least two observations. This verifies exchangeability
    support only; blocking does not adjust for a split or batch effect.
    """
    if len(groups) != len(strata) or not groups:
        raise InputValidationError("groups and permutation strata must be non-empty and aligned")
    if minimum_per_group_per_block < 2:
        raise InputValidationError("minimum block representation must be at least two")
    labels = [str(value).strip() for value in groups]
    blocks = [str(value).strip() for value in strata]
    if any(not value for value in labels + blocks):
        raise InputValidationError("groups and permutation strata must be non-blank")
    all_groups = sorted(set(labels))
    table: dict[str, dict[str, int]] = {}
    for block in sorted(set(blocks)):
        counts = Counter(label for label, observed_block in zip(labels, blocks) if observed_block == block)
        table[block] = {group: counts[group] for group in all_groups}
    inadequate = [
        f"{block}:{group}={count}"
        for block, counts in table.items()
        for group, count in counts.items()
        if count < minimum_per_group_per_block
    ]
    if inadequate:
        raise InputValidationError(
            "inadequate group representation within permutation block: " + ", ".join(inadequate)
        )
    return table


def permute(values: Sequence[object], index_map: Sequence[int]) -> list[object]:
    if len(values) != len(index_map) or sorted(index_map) != list(range(len(values))):
        raise InputValidationError("invalid permutation index map")
    return [values[index] for index in index_map]
