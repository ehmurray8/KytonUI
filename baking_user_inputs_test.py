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
          self.create_instrs_grid()
          self.create_num_pts_input()
          self.create_time_ints()
          self.create_file_input()
          self.create_confirm_btn()

     def create_instrs_grid(self):
          instrs_grid = tk.Frame(self)
          instrs_grid.pack()         
 
          sm125_lbl = tk.Label(instrs_grid)
          sm125_lbl["text"] = "Micron Optics SM125"
          sm125_lbl.grid(row=0, sticky="w")
          sm125_select = tk.Checkbutton(instrs_grid, variable=self.sm125_state)
          sm125_select.grid(row=0,column=2)

          gp700_lbl = tk.Label(instrs_grid)
          gp700_lbl["text"] = "Dicon GP700"
          gp700_lbl.grid(row=1, sticky="w")
          gp700_select = tk.Checkbutton(instrs_grid, variable=self.gp700_state)
          gp700_select.grid(row=1,column=2)

          temp340_lbl = tk.Label(instrs_grid)
          temp340_lbl["text"] = "340 Controller"
          temp340_lbl.grid(row=2, sticky="w")
          temp340_select = tk.Checkbutton(instrs_grid, variable=self.temp340_state)
          temp340_select.grid(row=2,column=2)

          delta_oven_lbl = tk.Label(instrs_grid)
          delta_oven_lbl["text"] = "Delta Oven"
          delta_oven_lbl.grid(row=3, sticky="w")
          delta_oven_select = tk.Checkbutton(instrs_grid, variable=self.delta_oven_state)
          delta_oven_select.grid(row=3,column=2)

          instrs_grid.grid_columnconfigure(1, minsize=50)
          instrs_grid.grid_columnconfigure(3, minsize=50)

     def create_num_pts_input(self):
          num_pts_frame = tk.Frame(self)
          num_pts_frame.pack()

          num_pts_lbl = tk.Label(num_pts_frame, text="Num points to average: ")
          num_pts_lbl.grid(row=0, sticky="w")
          self.num_pts_entry = tk.Entry(num_pts_frame, width=10)
          self.num_pts_entry.grid(row=0, column=2)       

          num_pts_frame.grid_columnconfigure(1, minsize=45)

     def create_time_ints(self):
          time_frame = tk.Frame(self)
          time_frame.pack()

          prim_time_lbl = tk.Label(time_frame, text="Primary time interval: ")
          prim_time_lbl.grid(row=0, sticky = "w")
          self.prim_time_entry = tk.Entry(time_frame, width=10)
          self.prim_time_entry.grid(row=0, column=1)
          prim_time_post_lbl = tk.Label(time_frame, text="hours")
          prim_time_post_lbl.grid(row=0, column=2)

          sec_time_lbl = tk.Label(time_frame, text="Secondary time interval: ");
          sec_time_lbl.grid(row=1, sticky = "w")
          self.sec_time_entry = tk.Entry(time_frame, width=10)
          self.sec_time_entry.grid(row=1, column=1)
          sec_time_post_lbl = tk.Label(time_frame, text="minutes")
          sec_time_post_lbl.grid(row=1, column=2)

     def create_file_input(self):
          file_frame = tk.Frame(self)
          file_frame.pack()

          file_lbl = tk.Label(file_frame, text="File name: ")
          file_lbl.grid(row=0, sticky="w")
          self.file_entry = tk.Entry(file_frame, width=25)
          self.file_entry.grid(row=0, column=1)

     def create_confirm_btn(self):
          self.confirm_button = tk.Button(self)
          self.confirm_button["text"] = "Confirm"
          self.confirm_button["command"] = self.confirm
          self.confirm_button.pack()
     
     def confirm(self):
          print("SM125: " + format_selected(self.sm125_state.get()))
          print("GP700: " + format_selected(self.gp700_state.get()))
          print("Temp340: " + format_selected(self.temp340_state.get()))
          print("Delta Oven: " + format_selected(self.delta_oven_state.get()))
          print("Points to average: " + self.num_pts_entry.get())
          print("Primary time interval: " + self.prim_time_entry.get())
          print("Secondary time interval: " + self.sec_time_entry.get())          
          print("File name: " + self.file_entry.get())

def format_selected(flag):
     if flag == 1: 
          return "On"
     else:
          return "Off"    


root = tk.Tk()
app = Application(master=root)
app.mainloop()
