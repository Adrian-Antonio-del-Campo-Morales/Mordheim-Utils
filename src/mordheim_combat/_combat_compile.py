"""Import facade for the native compile helpers.

The implementation moved to ``mordheim_combat.native._combat_compile``; this
module keeps the historical ``mordheim_combat._combat_compile`` path
resolvable so already-compiled native binaries keep importing it unchanged.
"""
from mordheim_combat.native._combat_compile import *  # noqa: F401,F403
