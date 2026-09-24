import { I18nContext } from "@src/features/campaign/i18n-context";
import { translate } from "@src/features/campaign/i18n-core";
/**
 * P6.2 component tests: the draft panel composes a warband draft through the
 * real kernel workflow with the artefact-shaped fake knowledge reader:
 * - the warband picker lists only KB-resolvable candidates;
 * - starting a draft shows the live composition status;
 * - commit is gated on draft legality and hands State #0 to the shell.
 */

import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { DraftPanel } from "@src/features/draft/DraftPanel";
import type { CampaignDocument } from "@domain/campaign/index";

afterEach(cleanup);

describe("P6.2 DraftPanel", () => {
  it("updates the legacy draft route and KB options when locale changes", () => {
    const view = (locale: "es" | "en") => <I18nContext.Provider value={{ locale, t: (message) => translate(message, locale) }}><DraftPanel onCommitted={() => undefined} /></I18nContext.Provider>;
    const { rerender } = render(view("es"));
    expect(screen.getByRole("option", { name: "Hermanas de Sigmar" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Crear borrador" })).toBeTruthy();
    rerender(view("en"));
    expect(screen.getByRole("option", { name: "Sisters of Sigmar" })).toBeTruthy();
    expect(screen.queryByText("Hermanas de Sigmar")).toBeNull();
    rerender(view("es"));
    expect(screen.getByRole("option", { name: "Hermanas de Sigmar" })).toBeTruthy();
  });

  it("lists only warband candidates the KB resolves", () => {
    render(<DraftPanel onCommitted={() => undefined} />);
    const select = screen.getByLabelText(/warband/i) as HTMLSelectElement;
    const values = Array.from(select.options).map((o) => o.value);
    // The fake reader resolves "sisters-of-sigmar"; the other nine static
    // candidates are filtered out by the workflow (never guessed).
    expect(values).toContain("sisters-of-sigmar");
    expect(values).toEqual(["", "sisters-of-sigmar"]);
  });

  it("starts a draft and shows the live composition status", async () => {
    const user = userEvent.setup();
    render(<DraftPanel onCommitted={() => undefined} />);
    await user.selectOptions(screen.getByLabelText(/warband/i), "sisters-of-sigmar");
    await user.click(screen.getByRole("button", { name: /start draft/i }));

    const status = await screen.findByText(/Models \d+\/\d+/);
    expect(status.textContent).toContain("Treasury");

    // The isolated legacy panel fixture still builds its legal starter roster.
    const commit = screen.getByRole("button", {
      name: /commit initial warband/i,
    }) as HTMLButtonElement;
    expect(commit.disabled).toBe(false);
  });

  it("exposes the live legality status before commit", async () => {
    const user = userEvent.setup();
    render(<DraftPanel onCommitted={() => undefined} />);
    await user.selectOptions(screen.getByLabelText(/warband/i), "sisters-of-sigmar");
    await user.click(screen.getByRole("button", { name: /start draft/i }));
    const commit = screen.getByRole("button", { name: /commit initial warband/i }) as HTMLButtonElement;
    expect(commit.disabled).toBe(false);
    expect(screen.getAllByRole("status")[0].textContent).toMatch(/Models/);
  });

  it("commits a legal draft and hands State #0 to the shell", async () => {
    const user = userEvent.setup();
    const received: { document: CampaignDocument | null } = { document: null };
    const onCommitted = (document: CampaignDocument): void => {
      received.document = document;
    };
    render(<DraftPanel onCommitted={onCommitted} />);
    await user.selectOptions(screen.getByLabelText(/warband/i), "sisters-of-sigmar");
    await user.click(screen.getByRole("button", { name: /start draft/i }));
    await user.click(screen.getByRole("button", { name: /commit initial warband/i }));
    expect(received.document).not.toBeNull();
    const committed = received.document;
    if (!committed) return;
    expect(committed.campaign.configuration.is_draft).toBe(false);
    expect(committed.campaign.current_state_number).toBe(0);
    expect(committed.campaign.states).toHaveLength(1);
    expect(committed.campaign.states[0].label).toBe("Initial Warband");
  });
});
