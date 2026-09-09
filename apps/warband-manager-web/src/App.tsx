// P5.2 vertical slice: import → display → edit → export.
// The shell renders the slice; campaign logic still lives in
// packages/typescript/{domain,application} via the feature's hook.
import { CampaignSlice } from "./features/campaign/CampaignSlice";

export function App() {
  return <CampaignSlice />;
}
