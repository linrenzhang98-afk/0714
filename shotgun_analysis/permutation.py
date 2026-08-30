"""Deterministic, optionally stratum-restricted permutation generation."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Hashable, Sequence

from .errors import InputValidationError


def restricted_permutations(
    n_samples: int,
    n_permutations: int,
    seed: int,
    strata: Sequence[Hashable] | None = None,
) -> list[list[int]]:
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
    rng = random.Random(seed)
    output: list[list[int]] = []
    for _ in range(n_permutations):
        permutation = list(range(n_samples))
        for indices in blocks.values():
            shuffled = list(indices)
            rng.shuffle(shuffled)
            for target, source in zip(indices, shuffled):
                permutation[target] = source
        output.append(permutation)
    return output


def permute(values: Sequence[object], index_map: Sequence[int]) -> list[object]:
    if len(values) != len(index_map) or sorted(index_map) != list(range(len(values))):
        raise InputValidationError("invalid permutation index map")
    return [values[index] for index in index_map]
