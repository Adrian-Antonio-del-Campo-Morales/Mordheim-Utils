"""campaign.domain.timeline_service: post-battle step navigation rules.

The sequential-access policy of the eight-step post-battle: which steps a
player may open, what advancing means and when the final review unlocks.
Pure over the ``PostBattleVM``; the controller applies the returned changes
to the state and notifies its views.
"""
from __future__ import annotations

from mordheim_campaign.domain.models import POST_BATTLE_STEPS, PostBattleVM


def accessible_steps(post: PostBattleVM) -> set[int]:
    """Steps the player may open: completed ones plus the active step.

    Completed steps may be revisited, but future steps are reached only
    through the sequential Continue action.
    """
    return set(post.completed_steps) | {post.active_step}


def select_step(post: PostBattleVM, index: int) -> bool:
    """Select a step if it is accessible; closes the final review.

    Returns whether the selection was applied.
    """
    if index not in accessible_steps(post):
        return False
    post.active_step = index
    post.review_open = False
    return True


def advance_step(post: PostBattleVM) -> bool:
    """Continue to the next step, or open the review after the last one."""
    current = post.active_step
    post.completed_steps.add(current)
    if current >= len(POST_BATTLE_STEPS) - 1:
        # Once Equipment is complete the eight-step sequence is done and the
        # app opens a confirmation diff.
        post.review_open = True
        return False
    post.active_step = current + 1
    post.review_open = False
    return True


def review_unlocked(post: PostBattleVM) -> bool:
    """The final review opens only when every step has been completed."""
    return len(post.completed_steps) >= len(POST_BATTLE_STEPS)


def open_review(post: PostBattleVM) -> bool:
    """Open the confirmation diff when the sequence is complete."""
    if not review_unlocked(post):
        return False
    post.review_open = True
    return True
