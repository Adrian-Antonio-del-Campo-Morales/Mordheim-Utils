"""Advancement write side: pending advances, KB tables, committed picks.

Threshold ladder comes from the KB (``advance_thresholds``); the tables from
``advancement_tables``; the skill/spell pools from ``catalog/skills`` and
``magic.yaml``. The example campaign's matriarch (23 XP, wizard) anchors the
roll scenarios.
"""
from __future__ import annotations

from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_campaign.application.state import make_example_state
from tests.campaign.test_post_battle_engine import _pending


def test_threshold_crossing_seeds_pending_advances():
    engine, state, _ = _pending()
    added = engine.sync_pending_advances()  # matriarch at 23 XP: the 20 rung
    assert added == 1
    row = state.campaign.post_battles[-1].pending_advances[0]
    assert row["warrior_id"] == "matriarch"
    assert row["table"] == "hero" and row["threshold"] == 20
    assert row["roll_total"] is None and not row["committed"]
    assert engine.sync_pending_advances() == 0  # idempotent


def test_add_xp_crossing_a_threshold_earns_an_advance():
    engine, state, _ = _pending()
    engine.add_xp("matriarch", 1)  # 23 -> 24: first sync inside add_xp seeds the 20 rung
    rows = state.campaign.post_battles[-1].pending_advances
    assert [row["threshold"] for row in rows] == [20]
    engine.add_xp("veriet", 10)  # 10 -> 20
    rows = state.campaign.post_battles[-1].pending_advances
    assert [row["warrior_id"] for row in rows] == ["matriarch", "veriet"]
    assert rows[1]["threshold"] == 20


def test_henchman_group_thresholds_and_shared_advance_row():
    engine, state, _ = _pending()
    engine.add_xp("novices", 4)  # 4 -> 8: first henchman rung
    rows = state.campaign.post_battles[-1].pending_advances
    assert rows and rows[0]["warrior_id"] == "novices"
    assert rows[0]["table"] == "henchman" and rows[0]["threshold"] == 8


def test_roll_11_offers_skill_and_spell_for_the_wizard_matriarch():
    engine, _state, _port = _pending()
    engine.sync_pending_advances()
    ok, _ = engine.resolve_pending_advance("matriarch", 11)
    assert ok
    kinds = {option.kind for option in engine.advance_options("matriarch")}
    assert kinds == {"choose_skill", "generate_spell"}  # wizard keeps the spell option


def test_non_wizard_heroes_lose_the_spell_option():
    engine, state, _ = _pending()
    engine.sync_pending_advances()
    engine.resolve_pending_advance("matriarch", 11)  # wizard's own row
    engine.add_xp("anna", 1)  # 19 -> 20
    engine.resolve_pending_advance("anna", 11)
    kinds = {option.kind for option in engine.advance_options("anna")}
    assert kinds == {"choose_skill"}


def test_commit_skill_validates_the_warriors_kb_tables():
    engine, state, _ = _pending()
    engine.sync_pending_advances()
    engine.resolve_pending_advance("matriarch", 11)
    ok, message = engine.commit_pending_advance("matriarch", option_kind="choose_skill", skill_name="Combat Master")
    assert ok, message
    assert "Combat Master" in next(w for w in state.campaign.warriors if w.id == "matriarch").skills
    # Committing twice is rejected (the advance is already applied).
    ok, _ = engine.commit_pending_advance("matriarch", option_kind="choose_skill", skill_name="Step Aside")
    assert not ok


def test_commit_spell_comes_from_the_wizards_lore():
    engine, state, port = _pending()
    engine.sync_pending_advances()
    engine.resolve_pending_advance("matriarch", 11)
    lore = port.wizard_lore("sigmarite-matriarch", state.campaign.band_id)
    spells = port.lore_spells(lore)
    assert lore and spells
    ok, message = engine.commit_pending_advance("matriarch", option_kind="generate_spell", spell_id=spells[0]["id"])
    assert ok, message
    assert spells[0]["name"] in next(w for w in state.campaign.warriors if w.id == "matriarch").skills
    # A non-wizard cannot learn spells.
    engine.add_xp("anna", 1)
    engine.resolve_pending_advance("anna", 12)
    ok, _ = engine.commit_pending_advance("anna", option_kind="generate_spell", spell_id=spells[0]["id"])
    assert not ok


def test_roll_8_needs_a_d6_subroll_and_commits_the_stat():
    engine, state, _ = _pending()
    engine.sync_pending_advances()
    outcome, _row = engine._pending_outcome("matriarch")  # roll_total None: outcome None
    assert outcome is None
    ok, message = engine.resolve_pending_advance("matriarch", 8, subroll=2)  # I for 1-3
    assert ok and "+1 I" in message
    matriarch = next(w for w in state.campaign.warriors if w.id == "matriarch")
    assert matriarch.stats["I"] == 5 and matriarch.stat_advances["I"] == 1


def test_roll_9_subroll_determines_W_or_T():
    engine, state, _ = _pending()
    engine.sync_pending_advances()
    ok, message = engine.resolve_pending_advance("matriarch", 9, subroll=5)  # T for 4-6
    assert ok and "+1 T" in message


def test_henchman_plus_one_cap_blocks_second_advance():
    engine, state, _ = _pending()
    engine.add_xp("novices", 12)  # 4 -> 16: rungs 8 and 16
    rows = state.campaign.post_battles[-1].pending_advances
    assert [row["threshold"] for row in rows] == [8, 16]
    # Roll 6 offers +1 BS / +1 WS (choose_one row).
    ok, _ = engine.resolve_pending_advance("novices", 6)
    assert ok
    options = engine.advance_options("novices")
    assert {o.kind for o in options} == {"characteristic_increase"} and len(options) == 2
    first_key = options[0].characteristic
    ok, message = engine.commit_pending_advance(
        "novices", option_kind="characteristic_increase", characteristic=first_key,
    )
    assert ok, message
    # Second rung, same characteristic: capped at starting+1.
    ok, _ = engine.resolve_pending_advance("novices", 6)
    assert ok
    ok, message = engine.commit_pending_advance(
        "novices", option_kind="characteristic_increase", characteristic=first_key,
    )
    assert not ok and "cap" in message


def test_henchman_deterministic_rows_commit_directly():
    engine, state, _ = _pending()
    engine.add_xp("novices", 4)  # 4 -> 8: first rung
    # Roll 8 gives +1 A, roll 9 +1 Ld deterministically; 2-4 give +1 I, 5 +1 S.
    ok, message = engine.resolve_pending_advance("novices", 8)
    assert ok and "+1 A" in message
    engine.add_xp("novices", 8)  # 8 -> 16: second rung
    ok, message = engine.resolve_pending_advance("novices", 5)
    assert ok and "+1 S" in message
    novices = next(w for w in state.campaign.warriors if w.id == "novices")
    assert novices.stat_advances["A"] == 1 and novices.stat_advances["S"] == 1


def test_hero_subroll_rows_6_8_9():
    engine, state, _ = _pending()
    engine.sync_pending_advances()
    # Hero 6: D6 1-3 -> +1 S, 4-6 -> +1 A.
    ok, message = engine.resolve_pending_advance("matriarch", 6, subroll=2)
    assert ok and "+1 S" in message


def test_racial_maximum_blocks_further_increases():
    engine, state, _ = _pending()
    engine.sync_pending_advances()  # matriarch row (hero: no henchman cap)
    matriarch = next(w for w in state.campaign.warriors if w.id == "matriarch")
    matriarch.stats["T"] = 4  # human racial max for T; hero roll 9 subroll 4-6 = +1 T
    ok, message = engine.resolve_pending_advance("matriarch", 9, subroll=6)
    assert not ok and "racial maximum" in message
    row = engine.post.pending_advance_for("matriarch")
    assert not row["committed"] and row["roll_total"] == 9  # stays pending for a reroll

def test_advancement_state_survives_save_load(tmp_path):
    engine, state, _ = _pending()
    engine.sync_pending_advances()
    engine.resolve_pending_advance("matriarch", 11)
    engine.commit_pending_advance("matriarch", option_kind="choose_skill", skill_name="Combat Master")
    path = save_and_load(state, tmp_path)
    post = path.campaign.pending_post_battle
    row = post.pending_advance_for("matriarch")
    assert row["committed"] and row["applied_label"] == "Skill: Combat Master"
    warrior = next(w for w in path.campaign.warriors if w.id == "matriarch")
    assert "Combat Master" in warrior.skills


def test_stat_advances_survive_save_load(tmp_path):
    engine, state, _ = _pending()
    engine.sync_pending_advances()
    engine.resolve_pending_advance("matriarch", 8, subroll=2)
    before = dict(next(w for w in state.campaign.warriors if w.id == "matriarch").stats)
    reloaded = save_and_load(state, tmp_path)
    warrior = next(w for w in reloaded.campaign.warriors if w.id == "matriarch")
    assert warrior.stats == before
    assert warrior.stat_advances.get("I") == 1


# ---------------------------------------------------------------- Lad's Got Talent


def test_roll_10_offers_the_promotion_option():
    engine, state, _ = _pending()
    engine.add_xp("novices", 4)  # first henchman rung
    ok, message = engine.resolve_pending_advance("novices", 10)
    assert ok and "Lad's Got Talent" in message
    options = engine.advance_options("novices")
    assert [(o.kind, o.label) for o in options] == [("promote_henchman", "Promote a member")]
    # Not auto-committed: the player must promote explicitly.
    assert not engine.post.pending_advance_for("novices")["committed"]


def test_promotion_splits_the_group_and_preserves_state():
    engine, state, _ = _pending()
    novices = next(w for w in state.campaign.warriors if w.id == "novices")
    novices.stats["WS"] = 3  # an earlier advance to preserve
    novices.stat_advances["WS"] = 1
    novices.experience = 8
    heroes_before = engine.projected_heroes()
    # The pending promotion row (KB row 10) grants the hero-slot allowance.
    engine.sync_pending_advances()
    engine.resolve_pending_advance("novices", 10)
    ok, message = engine.promote_henchman("novices", member_name="Novice Olaf")
    assert ok, message
    hero = next(w for w in state.campaign.warriors if w.kind == "hero" and "promoted" in w.id)
    assert hero.name == "Novice Olaf" and hero.kind == "hero"
    assert hero.experience == 8 and hero.stats["WS"] == 3 and hero.stat_advances["WS"] == 1
    assert novices.quantity == 1 and novices.kind == "henchman"
    assert engine.projected_heroes() == heroes_before + 1
    assert engine.projected_models() == 8  # split, not added
    # The pending advance continues on the promoted hero with 2 picks.
    row = engine.post.pending_advance_for(hero.id)
    assert row is not None, engine.post.pending_advances
    assert row["promotion_pending"] and engine.promotion_pick_budget(hero.id) == 2


def test_promotion_requires_two_skills_and_completes():
    engine, state, _ = _pending()
    engine.add_xp("novices", 4)
    engine.resolve_pending_advance("novices", 10)
    engine.promote_henchman("novices", member_name="Novice Olaf")
    hero = next(w for w in state.campaign.warriors if w.kind == "hero" and "promoted" in w.id)
    tables = engine.promotion_hero_tables(hero.id)
    assert "Combat" in tables
    skill = next(s for s in (str(r.get("name")) for r in engine.port.skills())
                 if engine.port.skill_table_label(engine.port.skill_by_name(s) or {}) == "Combat")
    ok, message = engine.commit_promotion_skill(hero.id, skill)
    assert ok and "1 promotion pick left" in message
    # Re-resolving mid-promotion does not treat the row as done.
    ok, message = engine.resolve_pending_advance(hero.id, 10)
    assert ok and "second skill" in message
    second = next(s for s in (str(r.get("name")) for r in engine.port.skills())
                  if s != skill and engine.port.skill_table_label(engine.port.skill_by_name(s) or {}) == "Combat")
    ok, message = engine.commit_promotion_skill(hero.id, second)
    assert ok and "completes the promotion" in message
    row = engine.post.pending_advance_for(hero.id)
    assert row["committed"] and "Promoted" in row["applied_label"]
    assert hero.kind == "hero" and len(hero.skills) >= 2
    # Budget exhausted: no third pick.
    ok, _ = engine.commit_promotion_skill(hero.id, skill)
    assert not ok


def test_promotion_skills_must_come_from_warband_hero_tables():
    engine, state, _ = _pending()
    engine.add_xp("novices", 4)
    engine.resolve_pending_advance("novices", 10)
    engine.promote_henchman("novices")
    hero = next(w for w in state.campaign.warriors if w.kind == "hero" and "promoted" in w.id)
    tables = set(engine.promotion_hero_tables(hero.id))
    outside = next(s for s in (str(r.get("name")) for r in engine.port.skills())
                   if engine.port.skill_table_label(engine.port.skill_by_name(s) or {}) not in tables)
    ok, message = engine.commit_promotion_skill(hero.id, outside)
    assert not ok and "hero skill tables" in message


def test_promotion_bypasses_the_static_hero_limit_once():
    engine, state, _ = _pending()
    engine.campaign.hero_limit = 4  # example roster fields 4 heroes
    engine.add_xp("novices", 4)
    engine.resolve_pending_advance("novices", 10)  # pending promotion row grants the allowance
    ok, message = engine.promote_henchman("novices", member_name="Novice Olaf")
    assert ok, message
    # A second simultaneous promotion would exceed it again.
    engine.add_xp("sisters", 2)  # 6 -> 8: first henchman rung
    engine.resolve_pending_advance("sisters", 10)
    ok, message = engine.promote_henchman("sisters")
    assert not ok and "hero maximum" in message


def test_promotion_of_a_single_model_group_is_rejected():
    engine, state, _ = _pending()
    novices = next(w for w in state.campaign.warriors if w.id == "novices")
    novices.quantity = 1
    engine.add_xp("novices", 4)
    engine.resolve_pending_advance("novices", 10)
    ok, message = engine.promote_henchman("novices")
    assert not ok and "cannot split" in message


def test_promotion_state_survives_save_load(tmp_path):
    engine, state, _ = _pending()
    engine.add_xp("novices", 4)
    engine.resolve_pending_advance("novices", 10)
    engine.promote_henchman("novices", member_name="Novice Olaf")
    hero = next(w for w in state.campaign.warriors if w.kind == "hero" and "promoted" in w.id)
    engine.commit_promotion_skill(hero.id, "Combat Master")
    from mordheim_campaign.persistence import load_campaign, save_campaign

    reloaded = load_campaign(save_campaign(tmp_path / "promo.mordheim", state))
    promoted = next(w for w in reloaded.campaign.warriors if w.kind == "hero" and "promoted" in w.id)
    assert "Combat Master" in promoted.skills
    row = reloaded.campaign.pending_post_battle.pending_advance_for(promoted.id)
    assert row["promotion_pending"] and row["promotion_skills"] == 1
    # Finishing on the reloaded engine completes the promotion.
    from mordheim_campaign.application.post_battle_engine import PostBattleEngine

    engine2 = PostBattleEngine(
        reloaded.campaign,  # not used; engine wants port first
        reloaded.campaign,
        reloaded.campaign.pending_post_battle,
    ) if False else PostBattleEngine(
        engine.port, reloaded.campaign, reloaded.campaign.pending_post_battle,
    )
    ok, message = engine2.commit_promotion_skill(promoted.id, "Step Aside")
    assert ok and "completes the promotion" in message
    assert reloaded.campaign.pending_post_battle.pending_advance_for(promoted.id)["committed"]


# --------------------------------------------------------------------- helpers

def save_and_load(state, tmp_path):
    from mordheim_campaign.persistence import load_campaign, save_campaign

    path = save_campaign(tmp_path / "adv.mordheim", state)
    return load_campaign(path)
