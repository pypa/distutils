# from more_itertools 8.13
def always_iterable(obj, base_type=(str, bytes)):
    if obj is None:
        return iter(())

    if (base_type is not None) and isinstance(obj, base_type):
        return iter((obj,))

    try:
        return iter(obj)
    except TypeError:
        return iter((obj,))
