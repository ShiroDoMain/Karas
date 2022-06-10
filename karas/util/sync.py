import asyncio
import functools
import threading
import inspect


def async_to_sync(obj, name):
    function = getattr(obj, name)
    main_loop = asyncio.get_event_loop()

    @functools.wraps(function)
    def _wrap(*args, **kwargs):
        coroutine = function(*args, **kwargs)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if threading.current_thread() is threading.main_thread() or not main_loop.is_running():
            if loop.is_running():
                return coroutine
            else:
                if inspect.iscoroutine(coroutine):
                    return loop.run_until_complete(coroutine)
        else:
            if inspect.iscoroutine(coroutine):
                if loop.is_running():
                    async def coro_wrapper():
                        return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coroutine, main_loop))
                    return coro_wrapper()
                else:
                    return asyncio.run_coroutine_threadsafe(coroutine, main_loop).result()
    setattr(obj, name, _wrap)


def async_to_sync_wrap(cls):
    attrs = [attr for attr in cls.__dict__ if not attr.startswith("_") and (
        inspect.iscoroutinefunction(getattr(cls, attr)) or inspect.isasyncgenfunction(getattr(cls, attr)))]
    for attr in attrs:
        async_to_sync(cls, attr)
    return cls
