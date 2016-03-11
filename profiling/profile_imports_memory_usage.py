
# Use with python package `memory_profiler`, e.g.::
#
#   python -m memory_profiler profiling/profile_imports_memory_usage.py
#

@profile
def foo():
    pass
    import ephem
    import lxml
    import voeventparse
    import voeventdb
    import fourpisky.visibility
    import fourpisky.comms
    import fourpisky.filters
    import fourpisky.formatting
    import fourpisky.triggers
    import fourpisky.utils
    import fourpisky.voevent

foo()