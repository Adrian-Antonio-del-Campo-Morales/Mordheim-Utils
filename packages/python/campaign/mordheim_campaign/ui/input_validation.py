"""Integer form inputs: tolerate editing, reject invalid submissions."""
from functools import wraps
import tkinter as tk

from mordheim_ui import themed_dialogs as messagebox
from mordheim_ui.i18n import tr


class IntegerInputError(ValueError):
    pass


class IntegerVar(tk.IntVar):
    def get(self):
        # IntVar.get accepts a float by truncating it. Read the raw Tcl value.
        try:
            return int(str(self._tk.globalgetvar(self._name)).strip())
        except (ValueError, TypeError, tk.TclError) as exc:
            raise IntegerInputError('Enter a whole number.') from exc


def numeric_action(method):
    @wraps(method)
    def run(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except IntegerInputError:
            previous = self.grab_current()
            try:
                messagebox.showerror(tr('Invalid number'), tr('Enter whole numbers in the numeric fields.'), parent=self)
            finally:
                if previous is not None and previous.winfo_exists():
                    previous.grab_set()
    return run


def numeric_preview(method):
    @wraps(method)
    def run(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except IntegerInputError:
            # An empty or incomplete value is normal while typing.
            return None
    return run
