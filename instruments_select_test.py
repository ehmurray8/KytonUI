import tkinter as tk
from tkinter import *

class Application(tk.Frame):
     def __init__(self, master):
          super().__init__(master)
          master.title("Kyton Baking")
          self.menu=Menu(master,tearoff=0)
          master.config(menu=self.menu)
          self.sm125_state = IntVar()
          self.gp700_state = IntVar()
          self.delta_oven_state = IntVar()
          self.temp340_state = IntVar()
          self.pack(side="top", fill="both", expand=True)
          self.create_widgets()

     def create_widgets(self):
          self.sm125_lbl = tk.Label(self)
          self.sm125_lbl["text"] = "Micron Optics SM125"
          self.sm125_lbl.grid(row=0, sticky="w")
          self.sm125_select = tk.Checkbutton(self, variable=self.sm125_state)
          self.sm125_select.grid(row=0,column=3)

          self.gp700_lbl = tk.Label(self)
          self.gp700_lbl["text"] = "Dicon GP700"
          self.gp700_lbl.grid(row=1, sticky="w")
          self.gp700_select = tk.Checkbutton(self, variable=self.gp700_state)
          self.gp700_select.grid(row=1,column=3)

          self.temp340_lbl = tk.Label(self)
          self.temp340_lbl["text"] = "340 Controller"
          self.temp340_lbl.grid(row=2, sticky="w")
          self.temp340_select = tk.Checkbutton(self, variable=self.temp340_state)
          self.temp340_select.grid(row=2,column=3)

          self.delta_oven_lbl = tk.Label(self)
          self.delta_oven_lbl["text"] = "Delta Oven"
          self.delta_oven_lbl.grid(row=3, sticky="w")
          self.delta_oven_select = tk.Checkbutton(self, variable=self.delta_oven_state)
          self.delta_oven_select.grid(row=3,column=3)

          self.confirm_button = tk.Button(self)
          self.confirm_button["text"] = "Confirm"
          self.confirm_button["command"] = self.confirm
          self.confirm_button.grid(row=4, column=2)

          self.grid_columnconfigure(1, minsize=50)
          self.grid_columnconfigure(4, minsize=50)

     def confirm(self):
          print("SM125: " + format_selected(self.sm125_state.get()))
          print("GP700: " + format_selected(self.gp700_state.get()))
          print("Temp340: " + format_selected(self.temp340_state.get()))
          print("Delta Oven: " + format_selected(self.delta_oven_state.get()))

def format_selected(flag):
     if flag == 1: 
          return "On"
     else:
          return "Off"    


root = tk.Tk()
app = Application(master=root)
app.mainloop()
