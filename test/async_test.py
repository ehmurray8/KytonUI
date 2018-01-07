import asyncio
import time

xxx = 1

async def test(future):
    t1 = time.time()
    await asyncio.sleep(5)
    t2 = time.time()
    final = t2 - t1
    future.set_result((final, "Hello"))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    future = asyncio.Future()
    asyncio.ensure_future(test(future))
    loop.run_until_complete(future)
    print(future.result())
    loop.close()
