"""Skeleton file as a starting point to build module.

Note that this file can be safely deleted if not needed!
"""


def fib(n: int) -> int:
    """Fibonacci example function

    Parameters
    ----------
    n : int

    Returns
    -------
    int
        n-th Fibonacci number

    """
    assert n > 0
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a
