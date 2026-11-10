Fixed a race in the MSVC compiler's lazy initialization when ``build_ext`` builds extensions in parallel.
Threads sharing a compiler could fail with ``AssertionError: don't init multiple times`` (most often on free-threaded Python).
