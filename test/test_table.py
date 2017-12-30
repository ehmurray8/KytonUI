import asyncio
import threading
import tkinter as tk
from table import Table

async def add_data_pt(data, listbox):
    for d in data:
        listbox.add_data(d)
        await asyncio.sleep(1.1)

def add_data_pts(data, listbox, new_loop):
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(add_data_pt(data, listbox))
    new_loop.close()

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Table Test")
    headers = ['car', 'repair', 'numbers', 'date']
    data = [('Hyundai', 'brakes', 1, "11/21/96"), ('Honda', 'light', 2, "11/21/97"),
                         ('Lexus', 'battery', 3, "12/4/98"), ('Benz', 'wiper', 4, "12/27/99"),
                         ('Ford', 'tire', 1, '1/2/98'), ('Chevy', 'air', 3, '1/3/78'),
                         ('Chrysler', 'piston', 7, "1/2/99"), ('Toyota', 'brake pedal', 1, "1/1/16"),
                         ('BMW', 'seat', 2, "1/2/92")]
    listbox = Table(root, headers)
    listbox.pack(fill='both', expand=True)
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=add_data_pts, args=(data, listbox, new_loop))
    t.start()
    root.mainloop()
