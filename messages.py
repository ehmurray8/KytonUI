import enum
import time
import datetime
from tkinter.font import Font
import tkinter as tk
import collections
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from constants import LOG_BACKGROUND_COLOR


class MessageType(enum.Enum):
    DEVELOPER = (5, "#170ad3")
    INFO = (4, "#FFFFFF")
    WARNING = (3, "#FFCC00")
    ERROR = (2, "#FF0000")
    CRITICAL = (1, "#FF8800")

    def __init__(self, filter_num: int, color: str):
        self.filter_num = filter_num
        self.color = color


class Message(object):

    def __init__(self, msg_type: MessageType, title: str, text: str):
        self.type = msg_type
        self.time = time.time()
        self.timestamp = datetime.datetime.fromtimestamp(self.time).strftime("%x %X")
        self.text = "{}: {}({})\n".format(self.timestamp, title, text)


class LogView(ttk.Frame):

    def __init__(self, container: ttk.Frame, **kwargs):
        super().__init__(container, **kwargs)
        self.message_types = [MessageType.INFO, MessageType.WARNING, MessageType.ERROR]
        self.all_types = self.message_types + [MessageType.CRITICAL, MessageType.DEVELOPER]
        self.messages = {}
        self.current_filter = MessageType.INFO
        for t in self.all_types:
            self.messages[t.name.title()] = []
        self.pack()
        header_frame = ttk.Frame(self)
        header_frame.pack(expand=True, fill=tk.BOTH)
        ttk.Label(header_frame, text="Program Log").pack(anchor=tk.W, side=tk.LEFT)

        self.filter = ttk.Combobox(header_frame, values=[mtype.name.title() for mtype in self.message_types])
        self.filter.config(state="readonly")
        self.filter.set(MessageType.INFO.name.title())
        self.filter.pack(anchor=tk.E, side=tk.RIGHT)

        self.filter.bind("<<ComboboxSelected>>", self.filter_msg)
        self.filter.pack(anchor=tk.E)
        self.log_view = ScrolledText(self, wrap=tk.WORD, background=LOG_BACKGROUND_COLOR)
        for t in self.all_types:
            self.log_view.tag_configure(t.name, font=Font(family="Helvetica", size=10), foreground=t.color)
        self.log_view.pack(expand=True, fill=tk.BOTH)

    def clear(self):
        self.log_view.config(state='normal')
        for t in self.all_types:
            try:
                self.log_view.tag_remove(t.name, "1.0", tk.END)
            except tk.TclError:
                pass
        self.log_view.delete("1.0", tk.END)

    def add_msg(self, msg: Message):
        self.messages[msg.type.name.title()].append((msg.time, msg.text))
        if  msg.type.filter_num <= self.current_filter.filter_num:
            self.write_msg(msg.text, msg.type.name)

    def write_msg(self, text: str, tag: str):
        self.log_view.config(state='normal')
        self.log_view.insert(tk.END, text)
        self.highlight_pattern(text, tag)
        self.log_view.config(state='disabled')

    def highlight_pattern(self, pattern, tag, start="1.0", end="end", regexp=False):
        '''Apply the given tag to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression according to Tcl's regular expression syntax.
        '''

        start = self.log_view.index(start)
        end = self.log_view.index(end)
        self.log_view.mark_set("matchStart", start)
        self.log_view.mark_set("matchEnd", start)
        self.log_view.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.log_view.search(pattern, "matchEnd", "searchLimit", count=count, regexp=regexp)
            if index == "": break
            if count.get() == 0: break # degenerate pattern which matches zero-length strings
            self.log_view.mark_set("matchStart", index)
            self.log_view.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.log_view.tag_add(tag, "matchStart", "matchEnd")

    def filter_msg(self, _):
        for t in self.all_types:
            selection = self.filter.current()
            if t.name.title() == self.message_types[selection].name.title():
                self.current_filter = t
        msgs = {}
        for t in self.all_types:
            if t.filter_num <= self.current_filter.filter_num:
                for msg in self.messages[t.name.title()]:
                    msgs[msg[0]] = (msg[1], t.name)

        self.clear()
        msgs = collections.OrderedDict(msgs.items())
        for time, (text, tag) in msgs.items():
            self.write_msg(text, tag)
