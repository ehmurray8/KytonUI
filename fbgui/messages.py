import enum
import os
import time
import datetime
from tkinter.font import Font
import tkinter as tk
import collections
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from fbgui.constants import LOG_BACKGROUND_COLOR

FILTER_TIME = 300.


class MessageType(enum.Enum):
    DEVELOPER = (5, "#3399FF")
    INFO = (4, "#FFFFFF")
    WARNING = (3, "#FFCC00")
    ERROR = (2, "#FF0000")
    CRITICAL = (1, "#FF8800")

    def __init__(self, filter_num: int, color: str):
        self.filter_num = filter_num
        self.color = color


class MessageDelay(enum.Enum):
    FIRST = 60.
    SHORT = 300.
    LONG = 600.
    MAX = 3600.


class SizeDict(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering function before accessing the keys"""

    def __init__(self, maxsize=50000, *args, **kwargs):
        self.store = dict()
        self.added_order = collections.deque()
        self.maxsize = maxsize
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        if key in self.added_order:
            self.added_order.remove(key)
        self.added_order.append(key)
        self.store[key] = value
        if len(self.store) > self.maxsize:
            rem_key = self.added_order.popleft()
            del self.store[rem_key]
        return key

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)


class Message(object):

    def __init__(self, msg_type: MessageType, title: str, text: str):
        self.type = msg_type
        self.time = time.time()
        self.timestamp = datetime.datetime.fromtimestamp(self.time).strftime("%x %X")
        self.text = "{}: {}({})\n".format(self.timestamp, title, text)
        self.msg = '{}({})\n'.format(title, text)


class LogView(ttk.Frame):

    def __init__(self, container: ttk.Frame, **kwargs):
        super().__init__(container, **kwargs)
        self.message_types = [MessageType.INFO, MessageType.WARNING, MessageType.ERROR]
        self.all_types = self.message_types + [MessageType.CRITICAL, MessageType.DEVELOPER]

        # Message stores
        self.messages = SizeDict()
        self.message_time = SizeDict(maxsize=1000)
        self.message_time_filter = SizeDict(maxsize=1000)

        self.first_click_time = time.time()
        self.num_clicks = 0
        self.showing = False

        self.current_filter = MessageType.INFO
        for t in self.all_types:
            self.messages[t.name.title()] = []
        self.pack()
        header_frame = ttk.Frame(self)
        header_frame.pack(expand=True, fill=tk.BOTH)
        header_lbl = ttk.Label(header_frame, text="Program Log")
        header_lbl.pack(anchor=tk.W, side=tk.LEFT)
        header_lbl.bind("<Button-1>", self.click_handler)

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
        ttk.Button(self, text="Export", command=self.export).pack(anchor=tk.CENTER)

    def click_handler(self, _):
        if time.time() - self.first_click_time > 15.:
            self.first_click_time = time.time()
            self.num_clicks = 0
        else:
            self.num_clicks += 1

        if self.num_clicks == 10:
            self.num_clicks = 0
            if not self.showing:
                self.message_types.append(MessageType.DEVELOPER)
            else:
                self.message_types.remove(MessageType.DEVELOPER)
            self.showing = not self.showing
            self.filter.config(values=[mtype.name.title() for mtype in self.message_types])

    def export(self):
        t = time.time()
        timestamp = datetime.datetime.fromtimestamp(t).strftime("%Y%m%dT%H%M%S")
        if not os.path.isdir("log"):
            os.mkdir("log")
        with open(os.path.join("log", "{}_log.txt".format(str(timestamp))), "w") as f:
            selection = self.filter.current()
            mtype = MessageType.INFO.filter_num
            if self.all_types[selection].name.title() == MessageType.DEVELOPER.name.title():
                mtype = MessageType.DEVELOPER.filter_num
            msgs = self.get_msgs(mtype)
            for t, (text, tag) in reversed(msgs.items()):
                f.write(text)

    def clear(self):
        self.log_view.config(state='normal')
        for t in self.all_types:
            try:
                self.log_view.tag_remove(t.name, "1.0", tk.END)
            except tk.TclError:
                pass
        self.log_view.delete("1.0", tk.END)

    def add_msg(self, msg: Message):
        if msg.msg in self.message_time and msg.time - self.message_time[msg.msg] < FILTER_TIME:
            if msg.msg not in self.message_time_filter:
                self.message_time_filter[msg.msg] = MessageDelay.FIRST
            else:
                curr_delay = self.message_time_filter[msg.msg]
                if curr_delay != MessageDelay.MAX:
                    idx = list(MessageDelay).index(curr_delay)
                    next_delay = list(MessageDelay)[idx+1]
                    self.message_time_filter[msg.msg] = next_delay
        elif msg.msg in self.message_time_filter:
            del self.message_time_filter[msg.msg]

        self.message_time[msg.msg] = msg.time
        self.messages[msg.type.name.title()].append((msg.time, msg.text))
        if msg.type.filter_num <= self.current_filter.filter_num:
            self.write_msg(msg.text, msg.type.name)

    def write_msg(self, text: str, tag: str, start="1.0"):
        self.log_view.config(state='normal')
        self.log_view.insert(start, text)
        self.highlight_pattern(text, tag)
        self.log_view.config(state='disabled')

    def highlight_pattern(self, pattern, tag, start="1.0", end="end", regexp=False):
        """
        Apply the given tag to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression according to Tcl's regular expression syntax.
        """
        start = self.log_view.index(start)
        end = self.log_view.index(end)
        self.log_view.mark_set("matchStart", start)
        self.log_view.mark_set("matchEnd", start)
        self.log_view.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.log_view.search(pattern, "matchEnd", "searchLimit", count=count, regexp=regexp)
            if index == "":
                break
            if count.get() == 0:
                break  # degenerate pattern which matches zero-length strings
            self.log_view.mark_set("matchStart", index)
            self.log_view.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.log_view.tag_add(tag, "matchStart", "matchEnd")

    def get_msgs(self, filter_num):
        msgs = {}
        for t in self.all_types:
            if t.filter_num <= filter_num:
                for msg in self.messages[t.name.title()]:
                    msgs[msg[0]] = (msg[1], t.name)
        return collections.OrderedDict(msgs.items(), key=lambda t: t[0])

    def filter_msg(self, _):
        for t in self.all_types:
            selection = self.filter.current()
            if t.name.title() == self.message_types[selection].name.title():
                self.current_filter = t
        msgs = self.get_msgs(self.current_filter.filter_num)
        self.clear()
        msg_items = list(msgs.items())
        for x in list(msg_items):
            if x[0] == 'key':
                msg_items.remove(x)
        msgs_sorted = reversed(sorted(msg_items, key=lambda x: x[0]))
        for t, (text, tag) in msgs_sorted:
            self.write_msg(text, tag, start=tk.END)
