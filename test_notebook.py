from tkinter import ttk
import tkinter as tk


class Test(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        notebook = ttk.Notebook()
        notebook.enable_traversal()
        notebook_inner = ttk.Notebook()
        frame = tk.Frame()
        frame1 = tk.Frame()
        notebook_inner.add(frame, text="Frame")
        notebook.add(notebook_inner, text="Test")
        notebook.add(frame1, text="Frame Outer")
        notebook.pack(side="top", fill="both", expand=True)

if __name__ == "__main__":
    TEST = Test()
    TEST.mainloop()
