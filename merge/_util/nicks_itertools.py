from typing import Iterator, TypeVar,  Generator
_T = TypeVar("_T")
def is_last(iterable:Iterator[_T])->Generator[tuple[bool, _T], None, None]:
    """Pass through all values from the given iterable, augmented by the
    information if there are more values to come after the current one
    (True), or if it is the last value (False).
    """
    # Get an iterator and pull the first value.
    try:
        last = next(iterable)
    except StopIteration:
        return
    # Run the iterator to exhaustion (starting from the second value).
    for val in iterable:
        # Report the *previous* value (more to come).
        yield False, last
        last = val
    # Report the last value.
    yield True, last