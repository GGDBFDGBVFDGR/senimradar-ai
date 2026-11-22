import random
from dataclasses import dataclass

from training.config import RANDOM_SEED, VALIDATION_FRACTION
from training.dataset import Example


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, item: str) -> None:
        self.parent.setdefault(item, item)

    def find(self, item: str) -> str:
        self.add(item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


@dataclass(frozen=True)
class SplitReport:
    train: list[Example]
    validation: list[Example]
    test: list[Example]
    dropped_train_overlap: int
    groups: int


def assign_groups(examples: list[Example]) -> dict[str, str]:
    """Keep translations and near-copies of one template in a single group."""

    union = UnionFind()
    template_owner: dict[str, str] = {}
    for example in examples:
        union.add(example.group_id)
        owner = template_owner.get(example.template)
        if owner is None:
            template_owner[example.template] = example.group_id
        else:
            union.union(owner, example.group_id)
    return {example.example_id: union.find(example.group_id) for example in examples}


def prepare_splits(train_rows: list[Example], test_rows: list[Example]) -> SplitReport:
    combined = [*train_rows, *test_rows]
    groups = assign_groups(combined)
    test_groups = {groups[item.example_id] for item in test_rows}
    trainable = [item for item in train_rows if groups[item.example_id] not in test_groups]
    dropped = len(train_rows) - len(trainable)
    by_group: dict[str, list[Example]] = {}
    for item in trainable:
        by_group.setdefault(groups[item.example_id], []).append(item)
    ordered = sorted(by_group)
    generator = random.Random(RANDOM_SEED)
    generator.shuffle(ordered)
    validation_count = max(1, round(len(ordered) * VALIDATION_FRACTION))
    validation_groups = set(ordered[:validation_count])
    train: list[Example] = []
    validation: list[Example] = []
    for group_id in ordered:
        target = validation if group_id in validation_groups else train
        target.extend(by_group[group_id])
    return SplitReport(
        train=train,
        validation=validation,
        test=list(test_rows),
        dropped_train_overlap=dropped,
        groups=len(ordered),
    )
