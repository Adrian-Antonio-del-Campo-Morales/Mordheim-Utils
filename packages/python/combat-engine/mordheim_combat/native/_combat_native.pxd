# Forward declarations for the mutually recursive core functions
# (resolve_weapon_c <-> apply_hit_defences_c).  Cython 3 requires non-extern
# forward declarations to live in the .pxd; the struct layouts are defined in
# the .pyx and only need to be known as incomplete types here.
from libc.stdint cimport int8_t
from libc.stdint cimport int16_t
from libc.stdint cimport uint32_t
from libc.stdint cimport uint64_t

cdef struct PCG32
cdef struct Rng
cdef struct EffectC
cdef struct SourceC
cdef struct FighterC
cdef struct DuelC
cdef struct StateC
cdef struct PreparedC


cdef int apply_hit_defences_c(DuelC* d, int atk_side, SourceC* src,
                              PreparedC* prepared, const int8_t* charging,
                              StateC* s_atk, StateC* s_def, Rng* rng,
                              const int* parry_rows, int parry_rows_n,
                              bint parry_given) except -1


cdef int resolve_weapon_c(DuelC* d, int atk_side, SourceC* src,
                          PreparedC* prepared, const int8_t* charging,
                          StateC* s_atk, StateC* s_def, Rng* rng,
                          bint first_round, const int8_t* phase_condition,
                          bint defences_resolved, const int* parry_rows,
                          int parry_rows_n, bint parry_given, object decisions,
                          bint always_accept, object attacker_py,
                          object defender_py, object observation) except -1