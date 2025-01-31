from __future__ import annotations

import dataclasses
import logging
from typing import Generator, Iterable

from dynamicprompts.commands.base import Command
from dynamicprompts.commands.literal_command import LiteralCommand
from dynamicprompts.enums import SamplingMethod

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class VariantOption:
    value: Command
    weight: float = 1.0


@dataclasses.dataclass
class VariantCommand(Command):
    variants: list[VariantOption]
    min_bound: int = 1
    max_bound: int = 1
    separator: str = ","
    sampling_method: SamplingMethod = SamplingMethod.DEFAULT

    def __post_init__(self):
        min_bound, max_bound = sorted((self.min_bound, self.max_bound))
        self.min_bound = max(0, min_bound)
        self.max_bound = min(len(self.variants), max_bound)

        self.min_bound = min(self.min_bound, self.max_bound)

    def __len__(self) -> int:
        return len(self.variants)

    def __getitem__(self, index: int) -> VariantOption:
        return self.variants[index]

    def __iter__(self) -> Iterable[VariantOption]:
        return iter(self.variants)

    def propagate_sampling_method(
        self,
        sampling_method: SamplingMethod = SamplingMethod.DEFAULT,
    ) -> None:
        super().propagate_sampling_method(sampling_method=sampling_method)

        for value in self.values:
            value.propagate_sampling_method(self.sampling_method)

    @property
    def weights(self) -> list[float]:
        return [p.weight for p in self.variants]

    @property
    def values(self) -> list[Command]:
        return [p.value for p in self.variants]

    @classmethod
    def from_literals_and_weights(
        cls,
        literals: list[str],
        weights: list[float] | None = None,
        min_bound: int = 1,
        max_bound: int = 1,
        separator: str = ",",
        sampling_method: SamplingMethod = SamplingMethod.DEFAULT,
    ) -> VariantCommand:
        vals = [LiteralCommand(str(v)) for v in literals]
        if weights is None:
            weights = [1.0] * len(vals)
        assert len(vals) == len(weights), "Must have same number of weights as values"
        return VariantCommand(
            variants=[VariantOption(v, w) for v, w in zip(vals, weights)],
            min_bound=min_bound,
            max_bound=max_bound,
            separator=separator,
            sampling_method=sampling_method,
        )

    def get_value_combinations(
        self,
        k: int,
        values=None,
    ) -> Generator[list[Command], None, None]:
        if values is None:
            values = self.values
        if k <= 0:
            yield []
        else:
            for value in values:
                other_values = [v for v in values if v != value]
                for item in self.get_value_combinations(k - 1, values=other_values):
                    yield [value] + item
