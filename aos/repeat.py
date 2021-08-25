# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import inspect
import logging

import time

logger = logging.getLogger(__name__)

TEN_SECONDS = 10.0
ONE_MINUTE = 60


def repeat_until(
    condition, timeout=TEN_SECONDS, func=None, fargs=None, fkwargs=None
):
    """
    Repeats :func: until :condition: is met.

    :param condition: predicate with no arguments
    :param timeout: timeout in seconds
    :param func: function to be called on each repeat
    :param fargs: function positional arguments
    :param fkwargs: function key-word arguments
    :return:
    """
    return repeat(
        stop_condition=condition,
        timeout=timeout,
        func=func,
        fargs=fargs,
        fkwargs=fkwargs,
    )


def repeat(
    func=None,
    fargs=None,
    fkwargs=None,
    stop_condition=None,
    timeout=TEN_SECONDS,
    max_delay=ONE_MINUTE,
    error_condition=None,
):
    """
    Repeats :func: until :stop_condition: is met.

    :param stop_condition: predicate with no arguments, stops repeats if returned
    `True`. If set to `None` - does not repeat.
    :param error_condition: predicate with no arguments, stops repeats if returned
    `True`.
    :param timeout: timeout in seconds
    :param func: function to be called on each repeat
    :param fargs: function positional arguments
    :param fkwargs: function key-word arguments
    :param max_delay: maximum delay between calls
    :return:
    """

    delay = 0.1

    if fargs is None:
        fargs = []

    if fkwargs is None:
        fkwargs = {}

    retval = _call_function(fargs, fkwargs, func)

    while _continue(stop_condition, error_condition, retval) and timeout > 0:
        logger.info(f"[repeat] waiting {delay}")

        time.sleep(delay)

        timeout -= delay
        delay = min(delay * 2, max_delay)

        retval = _call_function(fargs, fkwargs, func)

    if timeout <= 0:
        raise TimeoutError(f"Timed out waiting for {stop_condition.__name__}")

    return retval


def _call_function(fargs, fkwargs, func):
    retval = None
    if callable(func):
        retval = func(*fargs, **fkwargs)
        logger.debug(f"[repeat] Call {func.__name__} returned {retval}")
    return retval


def accepts_args(func):
    if callable(func):
        return len(inspect.signature(func).parameters) == 1
    return False


def args(func, arg):
    return [arg] if accepts_args(func) else []


def _continue(stop_condition, error_condition, retval):
    stop_args = args(stop_condition, retval)
    err_args = args(error_condition, retval)

    is_error = error_condition(*err_args) if callable(error_condition) else False
    should_continue = (
        not stop_condition(*stop_args) if callable(stop_condition) else False
    )

    return not is_error and should_continue
