import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry

# Globale Standardwerte
DEFAULT_ENTRY_WIDTH = 40
DEFAULT_FONT = ("Helvetica", 12)
HEADING_FONT = ("Helvetica", 16, "bold")
DEFAULT_BUTTON_FONT = ("Helvetica", 11, "bold")
DEFAULT_PADDING = {"padx": 5, "pady": 3}


def create_standard_entry(parent, textvariable=None, width=None, **kwargs):
    """
    Erzeugt ein Entry-Feld mit einheitlicher Formatierung.
    :param parent: Das übergeordnete Widget.
    :param textvariable: Optionales StringVar.
    :param width: Optional, sonst DEFAULT_ENTRY_WIDTH.
    :param kwargs: Weitere Optionen für ttk.Entry.
    :return: ttk.Entry
    """
    return ttk.Entry(
        parent,
        textvariable=textvariable,
        font=DEFAULT_FONT,
        width=width or DEFAULT_ENTRY_WIDTH,
        **kwargs
    )


def create_standard_label(parent, text, **kwargs):
    """
    Erzeugt ein Label mit einheitlicher Formatierung.
    :param parent: Das übergeordnete Widget.
    :param text: Der darzustellende Text.
    :param kwargs: Weitere Optionen für ttk.Label.
    :return: ttk.Label
    """
    return ttk.Label(
        parent,
        text=text,
        font=DEFAULT_FONT,
        **kwargs
    )

def create_header_label(parent, text, **kwargs):
    """
    Erzeugt ein Label mit einheitlicher Formatierung.
    :param parent: Das übergeordnete Widget.
    :param text: Der darzustellende Text.
    :param kwargs: Weitere Optionen für ttk.Label.
    :return: ttk.Label
    """
    return ttk.Label(
        parent,
        text=text,
        font=HEADING_FONT,
        justify="left",
        **kwargs
    )

def create_standard_button(parent, text, command=None, **kwargs):
    """
    Erzeugt einen Button mit einheitlicher Formatierung.
    :param parent: Das übergeordnete Widget.
    :param text: Button-Beschriftung.
    :param command: Callback-Funktion.
    :param kwargs: Weitere Optionen für ttk.Button.
    :return: ttk.Button
    """
    return ttk.Button(
        parent,
        text=text,
        command=command,
        **kwargs
    )


def apply_standard_padding(widget):
    """
    Fügt einheitliches Padding zu einem Widget hinzu.
    :param widget: Das Widget.
    :return: Padding-Dict für grid/place/pack.
    """
    return DEFAULT_PADDING.copy()

def create_spinbox(parent, from_, to, textvariable=None, width=4, font=("Helvetica", 12), **kwargs):
    return tk.Spinbox(parent, from_=from_, to=to, width=width, textvariable=textvariable, 
                    font=font, format="%02.0f", **kwargs)

def create_date_entry(parent, date=None, **kwargs):
    entry = DateEntry(parent, date_pattern="dd.MM.yyyy", locale="de_DE", font=("Helvetica", 12), **kwargs)
    if date:
        entry.set_date(date)
    return entry
