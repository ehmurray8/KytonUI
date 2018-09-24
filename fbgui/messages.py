import enum
import os
import time
import datetime
import collections
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font
import tkinter as tk
from typing import Optional, Dict, List
from fbgui.constants import LOG_BACKGROUND_COLOR

#: Amount of time in between messages to enable the filtering
FILTER_TIME = 300.


class MessageType(enum.Enum):
    """
    Type of Message to log, used for coloring and filtering of messages.
    """
    DEVELOPER = (5, "#3399FF")
    INFO = (4, "#FFFFFF")
    WARNING = (3, "#FFCC00")
    ERROR = (2, "#FF0000")
    CRITICAL = (1, "#FF8800")

    def __init__(self, filter_num: int, color: str):
        """
        Createa a Message Type.

        :param filter_num: Level of filtering, lower numbers are more important
        :param color: the color to write the message as
        """
        self.filter_num = filter_num
        self.color = color


class MessageDelay(enum.Enum):
    """Length of delay before repeating a message if filtering is enabled."""
    FIRST = 60.
    SHORT = 300.
    LONG = 600.
    MAX = 3600.


class SizeDict(collections.MutableMapping):
    """
    A dictionary of max length that removes FIFO when the max size is reached.

    :ivar dict store: dictionary for storing key value pairs
    :ivar collections.deque added_order: FIFO queue of the keys used to keep a fixed length
    """

    def __init__(self, maxsize: int=50000):
        """
        Initializes dictionary and queue.

        :param maxsize: maximum number of elements in the dictionary
        """
        self.store = dict()
        self.added_order = collections.deque()
        self.maxsize = maxsize

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        """
        Add key value mapping to the dictionary, remove first added element if dictionary is full.

        :param key: key of the mapping
        :param value: value of the mapping
        :return: the key
        """
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
    """
    Message object contains info about a log message.

    :ivar time: unix timestamp in seconds of when the message was created
    :ivar msg: Test of the message without the timestamp included
    """

    def __init__(self, msg_type: MessageType, title: Optional[str], text: str):
        """
        Create a message, and log the time it was creaeted.

        :param MessageType msg_type: type of message
        :param str title: title of the message, can be None
        :param str text: text of the message
        """
        self.type = msg_type
        self.time = time.time()
        timestamp = datetime.datetime.fromtimestamp(self.time).strftime("%x %X")
        if title is None:
            self.text = "{}: {}\n".format(timestamp, text)
        else:
            self.text = "{}: {} - {}\n".format(timestamp, title, text)
        self.msg = '{} - {}\n'.format(title, text)


class LogView(ttk.Frame):
    """
    Widget for the program log messages, ttk Frame implementation.

    :ivar List[MessageType] message_types: the MessageTypes to include in the filter combobox
    :ivar List[MessageType] all_types: a list of all the message types
    :ivar List[MessageDelay] message_delays: a list of all of the message delays
    :ivar Dict[str: collections.deque] messages: mapping of message type title string to deques of fixed
                                                 size containing messages' body
    :ivar Dict[str: float] message_time: message body without timestamp mapped to time in s
    :ivar Dict[str: MessageDelay] message_time_filer: message body without timestamp mapped to MessageDelay
    :ivar float first_click_time: the time the header text was first clicked (Used for developer messages)
    :ivar int num_clicks: the number of times the header text was clicked within the specified time (Used for dev msgs)
    :ivar bool showing: True if developer messages are in the filter, False otherwise
    :ivar MessageType current_filter: the current message type to filter messages
    :ivar ttk.Combobox filter_box: the combobox tkinter widget used for selecting a filter level
    :ivar ttk.ScrolledText log_view: the scrolled text tkinter widget used for displaying log messages
    """

    def __init__(self, container: ttk.Frame, **kwargs):
        """
        Setup the log view widgets, and the data structures for storing messages.

        :param container: parent frame
        :param kwargs: additional arguments for the Frame
        """
        super().__init__(container, **kwargs)
        self.message_types = [MessageType.INFO, MessageType.WARNING, MessageType.ERROR]
        self.all_types = self.message_types + [MessageType.CRITICAL, MessageType.DEVELOPER]
        self.message_delays = [MessageDelay.FIRST, MessageDelay.SHORT, MessageDelay.LONG, MessageDelay.MAX]

        self.messages = {}
        self.message_time = SizeDict(maxsize=1000)  # type: Dict[str, float]
        self.message_time_filter = SizeDict(maxsize=1000)  # type: Dict[str, MessageDelay]

        self.first_click_time = time.time()
        self.num_clicks = 0
        self.showing = False

        self.current_filter = MessageType.INFO
        for t in self.all_types:
            self.messages[t.name.title()] = collections.deque(maxlen=25000)
        self.pack()
        header_frame = ttk.Frame(self)
        header_frame.pack(expand=True, fill=tk.BOTH)
        header_lbl = ttk.Label(header_frame, text="Program Log")
        header_lbl.pack(anchor=tk.W, side=tk.LEFT)
        header_lbl.bind("<Button-1>", self.click_handler)

        self.filter_box = ttk.Combobox(header_frame, values=[mtype.name.title() for mtype in self.message_types])
        self.filter_box.config(state="readonly")
        self.filter_box.set(MessageType.INFO.name.title())
        self.filter_box.pack(anchor=tk.E, side=tk.RIGHT)

        self.filter_box.bind("<<ComboboxSelected>>", self.filter_msg)
        self.filter_box.pack(anchor=tk.E)
        self.log_view = ScrolledText(self, wrap=tk.WORD, background=LOG_BACKGROUND_COLOR)
        for t in self.all_types:
            self.log_view.tag_configure(t.name, font=Font(family="Helvetica", size=10), foreground=t.color)
        self.log_view.pack(expand=True, fill=tk.BOTH)
        ttk.Button(self, text="Export", command=self.export).pack(anchor=tk.CENTER)

    def click_handler(self, _):
        """Click handler for the Program Log header to allow the user to view developer messages."""
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
            self.filter_box.config(values=[mtype.name.title() for mtype in self.message_types])

    def export(self):
        """Export the messages to a log text file in the log folder."""
        t = time.time()
        timestamp = datetime.datetime.fromtimestamp(t).strftime("%Y%m%dT%H%M%S")
        if not os.path.isdir("log"):
            os.mkdir("log")
        with open(os.path.join("log", "{}_log.txt".format(str(timestamp))), "w") as f:
            mtype = MessageType.INFO.filter_num
            if MessageType.DEVELOPER in self.message_types:
                mtype = MessageType.DEVELOPER.filter_num
            msgs = self.get_msgs(mtype)
            msgs_sorted = sort_messages(msgs)
            for t, (text, tag) in msgs_sorted:
                f.write(text)

    def clear(self):
        """Clear the log view scrolled text."""
        self.log_view.config(state='normal')
        for t in self.all_types:
            try:
                self.log_view.tag_remove(t.name, "1.0", tk.END)
            except tk.TclError:
                pass
        self.log_view.delete("1.0", tk.END)

    def add_msg(self, msg: Message):
        """
        Add the msg to the log view, and the message store data structures.

        :param msg: message to add to the log view
        """
        if msg.msg in self.message_time:
            if msg.time - self.message_time[msg.msg] > FILTER_TIME:
                del self.message_time[msg.msg]
            else:
                if msg.msg not in self.message_time_filter:
                    self.message_time_filter[msg.msg] = MessageDelay.FIRST
                else:
                    elapsed_time = msg.time - self.message_time[msg.msg]
                    if elapsed_time > self.message_time_filter[msg.msg].value:
                        self.messages[msg.type.name.title()].append((msg.time, msg.text))
                        self.message_time[msg.msg] = msg.time
                        if msg.type.filter_num <= self.current_filter.filter_num:
                            self.write_msg(msg.text, msg.type.name)
                        if self.message_time_filter[msg.msg] != MessageDelay.MAX:
                            self.message_time_filter[msg.msg] = \
                                self.message_delays[self.message_delays.index(self.message_time_filter[msg.msg])+1]
        else:
            self.message_time[msg.msg] = msg.time
            self.messages[msg.type.name.title()].append((msg.time, msg.text))
            if msg.type.filter_num <= self.current_filter.filter_num:
                self.write_msg(msg.text, msg.type.name)

    def write_msg(self, text: str, tag: str, start: str="1.0"):
        """
        Write the text to the Scrolled Text tkinter widget, color it based on the tag, add it to the beginning
        if start is '1.0', if start tk.END add it to the end.

        :param text: text to write to the scrolled text view
        :param tag: name of the tag that defines the style for the text, based on MessageType
        :param start: the position to start writing the text
        """
        self.log_view.config(state='normal')
        self.log_view.insert(start, text)
        self.highlight_pattern(text, tag)
        self.log_view.config(state='disabled')

    def highlight_pattern(self, pattern: str, tag: str, start: str="1.0", end: str="end", regexp: bool=False):
        """
        Apply the given tag to all text that matches the given pattern.

        :param pattern: pattern to match when looking to format the text using the tag.
        :param tag: tkinter scrolled text tag corresponding to a tk font
        :param start: where to start looking for the pattern from
        :param end: where to end looking for the pattern
        :param regexp: If True, pattern will be treated as a Tcl regular expression
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
                break
            self.log_view.mark_set("matchStart", index)
            self.log_view.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.log_view.tag_add(tag, "matchStart", "matchEnd")

    def get_msgs(self, filter_num: int) -> collections.OrderedDict:
        """
        Get all of the messages that have a filter number less than or equal the filter number.

        :param filter_num: the number used for filtering messages
        :return: time mapped to (text, tag) for all filtered messages
        """
        msgs = {}
        for _type in self.all_types:
            if _type.filter_num <= filter_num:
                for msg in self.messages[_type.name.title()]:
                    msgs[msg[0]] = (msg[1], _type.name)
        return collections.OrderedDict(msgs.items(), key=lambda t: t[0])

    def filter_msg(self, _):
        """Filters messages when the filter combobox value is changed."""
        for t in self.all_types:
            selection = self.filter_box.current()
            if t.name.title() == self.message_types[selection].name.title():
                self.current_filter = t
        msgs = self.get_msgs(self.current_filter.filter_num)
        self.clear()
        msgs_sorted = sort_messages(msgs)
        for t, (text, tag) in msgs_sorted:
            self.write_msg(text, tag, start=tk.END)


def sort_messages(msgs):
    msg_items = list(msgs.items())
    for item in list(msg_items):
        if item[0] == 'key':
            msg_items.remove(item)
    return reversed(sorted(msg_items, key=lambda x: x[0]))
