import asyncio
import threading
import tkinter as tk
from table import Table


async def add_data_pt(data, lbox):
    for d in data:
        lbox.add_data(d)
        await asyncio.sleep(1.1)
    await asyncio.sleep(1.1)
    lbox.reset()
    lbox.setup_headers(headers)


def add_data_pts(data, lbox, nloop):
    asyncio.set_event_loop(nloop)
    new_loop.run_until_complete(add_data_pt(data, lbox))
    new_loop.close()


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
    t = threading.Thread(target=add_data_pts, args=(d, listbox, new_loop))
    t.start()
    root.mainloop()
