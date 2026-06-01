from __future__ import annotations

import pytest

from mse.fsm import (
    ProjectFSMError,
    assert_both_members_bound,
    on_member_bound,
    on_release,
)
from mse.models import InitiatorRole, ProjectStatus, TutoringProject


def _project(**kwargs) -> TutoringProject:
    base = dict(
        id="p1",
        title="test",
        initiator_role=InitiatorRole.ADVISOR,
        advisor_id="a1",
        student_email="s@test.com",
        status=ProjectStatus.DRAFT,
    )
    base.update(kwargs)
    return TutoringProject(**base)


def test_on_member_bound_active_when_complete():
    p = _project(student_id="s1", rule_base_ids=["r1"])
    assert on_member_bound(p) == ProjectStatus.ACTIVE


def test_on_member_bound_pending_when_missing_student():
    p = _project(advisor_id="a1", student_id=None)
    assert on_member_bound(p) == ProjectStatus.PENDING_MEMBER


def test_assert_both_members_bound_raises():
    p = _project(student_id=None)
    with pytest.raises(ProjectFSMError):
        assert_both_members_bound(p)


def test_on_release_passed():
    p = _project(status=ProjectStatus.ANALYZING)
    assert on_release(p, True) == ProjectStatus.AWAITING_ADVISOR


def test_on_release_failed():
    p = _project(status=ProjectStatus.ANALYZING)
    assert on_release(p, False) == ProjectStatus.ACTIVE
