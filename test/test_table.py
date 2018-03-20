import asyncio
import threading
import tkinter as tk

from fbgui.table import Table


async def add_data_pt(data, lbox, mutex):
    for i, d in enumerate(data):
        lbox.add_data(d)
        await asyncio.sleep(1.1)
        if i == 4:
            print("Bye")
            mutex.release()

    await asyncio.sleep(1.1)
    lbox.reset()
    headers.pop()
    lbox.setup_headers(headers)


def add_data_pts(data, lbox, nloop, mutex):
    asyncio.set_event_loop(nloop)
    new_loop.run_until_complete(add_data_pt(data, lbox, mutex))
    new_loop.close()


def test(mutex):
    mutex.acquire()
    print("Hello")


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Table Test")
    headers = ['car', 'repair', 'numbers', 'date']
    d = [('Hyundai', 'brakes', 1, "11/21/96"), ('Honda', 'light', 2, "11/21/97"),
                         ('Lexus', 'battery', 3, "12/4/98"), ('Benz', 'wiper', 4, "12/27/99"),
                         ('Ford', 'tire', 1, '1/2/98'), ('Chevy', 'air', 3, '1/3/78'),
                         ('Chrysler', 'piston', 7, "1/2/99"), ('Toyota', 'brake pedal', 1, "1/1/16"),
                         ('BMW', 'seat', 2, "1/2/92")]
    listbox = Table()
    listbox.setup_headers(headers)
    listbox.pack(fill='both', expand=True)
    new_loop = asyncio.new_event_loop()
    mutex = threading.Semaphore(0)
    t = threading.Thread(target=add_data_pts, args=(d, listbox, new_loop, mutex))
    t.start()
    threading.Thread(target=test, args=(mutex,)).start()
    root.mainloop()
