# Warband Manager product parity

Desktop reference: `27dcf73e000a0aba42a8e5b591b914de57133c90`.
The machine-readable inventory is `manifest.json`. `integrated` means reachable
from the product shell; `verified` additionally requires browser and semantic
evidence. Test-migration owners maintain test evidence independently.

Known blocking gap: TypeScript post-battle currently records generic payloads
and advances eight markers. It does not yet implement the desktop's complete
injury, experience, exploration, search, equipment-obligation, follow-up and
commit semantics. The UI must not describe that sequence as product parity.

Serious-injury D66/D6 resolution now uses the generated KB and records the
battle number. Unsupported outcome effects remain parked as follow-ups rather
than being silently treated as complete.
