import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { describe, expect, it } from "vitest";

import type { Warrior } from "./types";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { WarriorCard } from "./WarriorCard";

describe("WarriorCard hireling abilities", () => {
  it("resolves a Hired Sword subtitle from the hireling catalogue", () => {
    const profileId = "hireling.hired-sword.ogre-bodyguard";
    const warrior = { id: `${profileId}#1`, name: "Ogro Guardaespaldas", profile_name: "Ogre Bodyguard", profile_id: profileId, kind: "hireling", stats: {}, equipment: [], skills: [], experience: 0, cost: 80 } as Warrior;
    const knowledge = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [], campaign: { hirelings: { profiles: [{ id: profileId, names: { en: "Ogre Bodyguard", es: "Ogro Guardaespaldas" } }] } } });

    render(<WarriorCard warrior={warrior} knowledge={knowledge} locale="es" />);
    expect(screen.getAllByText("Ogro Guardaespaldas")).toHaveLength(2);
    expect(screen.queryByText(/traducción pendiente/i)).not.toBeInTheDocument();
  });

  it("shows localized inherent rules for a hireling loaded from an older campaign", () => {
    const profileId = "hireling.hired-sword.elf-ranger";
    const ruleId = `${profileId}.rule.seeker`;
    const sightId = `${profileId}.rule.excellent-sight`;
    const warrior = { id: `${profileId}#1`, name: "Elf Ranger", profile_name: "Elf Ranger", profile_id: profileId, kind: "hireling", stats: {}, equipment: [], skills: ["Hireling.hired-Sword.elf-Ranger.rule.excellent-Sight"], experience: 0, cost: 40 } as Warrior;
    const knowledge = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [], campaign: { hirelings: {
      profiles: [{ id: profileId, rule_ids: [ruleId, sightId, `${profileId}.rule.campaign-eligibility`] }],
      rules: [
        { id: ruleId, name: "Seeker", names: { en: "Seeker", es: "Buscador" }, effects: { es: "Permite modificar un dado de exploración." } },
        { id: sightId, name: "Excellent Sight", names: { en: "Excellent Sight", es: "Vista Excepcional" }, effects: { es: "Detecta enemigos ocultos al doble de distancia." } },
      ],
    } } });

    render(<WarriorCard warrior={warrior} knowledge={knowledge} locale="es" />);
    expect(screen.getByText("Buscador")).toHaveAttribute("data-tooltip", "Permite modificar un dado de exploración.");
    expect(screen.getByText("Vista Excepcional")).toHaveAttribute("data-tooltip", "Detecta enemigos ocultos al doble de distancia.");
    expect(screen.queryByText(/hireling\.hired-sword/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/campaign-eligibility/)).not.toBeInTheDocument();
  });
});

describe("WarriorCard canonical ability labels", () => {
  it("shows Blessed Sight once through either profile-rule or mechanic id", () => {
    const warrior = { id: "augur#1", name: "Augur", profile_name: "Augur", profile_id: "augur", kind: "hero", stats: {}, equipment: [], skills: ["augur--blessed-sight", "skill.blessed-sight"], experience: 0, cost: 40 } as Warrior;
    const knowledge = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "mordheim", bands: [], profiles: [], items: [],
      skills: [{ id: "skill.blessed-sight", names: { en: "Blessed Sight", es: "Vista Bendecida" } }],
      rules_prose: { "profile-special-rules": [{ id: "augur--blessed-sight", applies_to: { profile_ids: ["augur"] }, names: { en: "Blessed Sight", es: "Vista Bendecida" } }] },
    });

    render(<WarriorCard warrior={warrior} knowledge={knowledge} locale="es" />);
    expect(screen.getAllByText("Vista Bendecida")).toHaveLength(1);
    expect(screen.queryByText(/skill\.blessed-sight/i)).not.toBeInTheDocument();
  });

  it("shows an active absence and the battles remaining on the roster", () => {
    const warrior = { id: "sigrid", name: "Sigrid", profile_name: "Sister", kind: "hero", stats: {}, equipment: [], skills: [], experience: 0, cost: 40, games_to_miss: 2, absence_reason: "deep_wound" } as Warrior;
    render(<WarriorCard warrior={warrior} locale="es" />);
    expect(screen.getByText("AUSENCIA")).toBeInTheDocument();
    expect(screen.getByText("Herida Profunda · se pierde 2 batalla(s) más")).toBeInTheDocument();
  });
});
