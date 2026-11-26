"""约束集合：每个 rule_id 一个可单独测试的判定。"""

from .consecutive import consecutive_findings
from .coverage import coverage_findings
from .fairness import fairness_counts, fairness_finding, weight_of
from .leave import leave_conflicts
from .rest import rest_findings
from .skill import double_bookings, skill_mismatches

__all__ = [
    "consecutive_findings",
    "coverage_findings",
    "double_bookings",
    "fairness_counts",
    "fairness_finding",
    "leave_conflicts",
    "rest_findings",
    "skill_mismatches",
    "weight_of",
]
