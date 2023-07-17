import typing as t
from dataclasses import dataclass, field


@dataclass
class Report:
    row_count: int = 0
    forward_primers_trimmed: t.List[int] = field(
        default_factory=list, repr=False, hash=False
    )
    reverse_primers_trimmed: t.List[int] = field(
        default_factory=list, repr=False, hash=False
    )
    scanning_summary: t.List[str] = field(
        default_factory=list, repr=False, hash=False, init=True
    )

    @property
    def both_trimmed(self) -> t.List[int]:
        both = list(
            set(self.forward_primers_trimmed) & set(self.reverse_primers_trimmed)
        )
        both.sort()
        return both

    def add_row(
        self,
        row_id: int,
        has_trimmed_forward_primer: bool,
        has_trimmed_reverse_primer: bool,
    ):
        self.row_count += 1
        if has_trimmed_forward_primer:
            self.forward_primers_trimmed.append(row_id)
        if has_trimmed_reverse_primer:
            self.reverse_primers_trimmed.append(row_id)
        return

    def add_scanning_summary(self, scanning_summary: t.List[str]):
        self.scanning_summary = scanning_summary
        return

    def add_null_data_summary(self, null_data_summary: str):
        self.scanning_summary.append(null_data_summary)
        return

    def summary(self) -> str:
        summary = self.scanning_summary.copy()
        total = self.row_count
        self.forward_primers_trimmed.sort()
        self.reverse_primers_trimmed.sort()
        summary.append(
            f"Forward primer trimmed in {len(self.forward_primers_trimmed)} of {total} sequences."
        )
        summary.append(
            f"Reverse primer trimmed in {len(self.reverse_primers_trimmed)} of {total} sequences."
        )
        summary.append(
            f"Forward + reverse primer trimmed in {len(self.both_trimmed)} out of {total} sequences."
        )
        return "\n".join(summary)
