# coding: utf-8
__author__ = 'petrmatuhov'

import asyncio


async def buz():
    print('start buz')
    await asyncio.sleep(1)
    print('stop buz')
    return 1


async def foo():
    print('start foo')
    await asyncio.sleep(2)
    print('stop foo')
    return 2


async def bar():
    print('start caller - bar')
    result = asyncio.ensure_future(foo())
    print('after foo')
    result2 = asyncio.ensure_future(buz())
    print('after buz')

    results = asyncio.gather(result, result2)
    return await results


loop = asyncio.get_event_loop()
future = bar()
loop.run_until_complete(future)

print(future)
