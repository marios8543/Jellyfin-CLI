from urwid import Button as urwid_button
from urwid import SelectableIcon as urwid_selectable
from urwid import Text
from urwid import Columns
from urwid.text_layout import calc_coords
from urwid import WidgetWrap
from urwid.widget import FLOW
from urwid.command_map import ACTIVATE
from urwid.signals import connect_signal
from urwid.split_repr import python3_repr
from urwid.util import is_mouse_press

class SelectableIconBg(Text):
    ignore_focus = False
    _selectable = True
    def __init__(self, text, cursor_position=0):
        super().__init__(text)
        self._text = text
        self._cursor_position = cursor_position

    def render(self, size, focus=False):
        if focus:
            super().set_text(("bg_inverted", self._text))
        else:
            super().set_text(self._text)
        c = super().render(size, focus)
        return c

    
    def keypress(self, size, key):
        return key

class ButtonNoArrows(WidgetWrap):
    def sizing(self):
        return frozenset([FLOW])

    button_left = Text("")
    button_right = Text("")

    signals = ["click"]

    def __init__(self, label, on_press=None, user_data=None):
        """
        :param label: markup for button label
        :param on_press: shorthand for connect_signal()
                         function call for a single callback
        :param user_data: user_data for on_press
        Signals supported: ``'click'``
        Register signal handler with::
          urwid.connect_signal(button, 'click', callback, user_data)
        where callback is callback(button [,user_data])
        Unregister signal handlers with::
          urwid.disconnect_signal(button, 'click', callback, user_data)
        >>> Button(u"Ok")
        <Button selectable flow widget 'Ok'>
        >>> b = Button("Cancel")
        >>> b.render((15,), focus=True).text # ... = b in Python 3
        [...'< Cancel      >']
        """
        self._label = SelectableIconBg("", 0)
        cols = Columns([
            ('fixed', 1, self.button_left),
            self._label,
            ('fixed', 1, self.button_right)],
            dividechars=1)
        super().__init__(cols)

        # The old way of listening for a change was to pass the callback
        # in to the constructor.  Just convert it to the new way:
        if on_press:
            connect_signal(self, 'click', on_press, user_data)

        self.set_label(label)

    def _repr_words(self):
        # include button.label in repr(button)
        return super()._repr_words() + [
            python3_repr(self.label)]

    def set_label(self, label):
        """
        Change the button label.
        label -- markup for button label
        >>> b = Button("Ok")
        >>> b.set_label(u"Yup yup")
        >>> b
        <Button selectable flow widget 'Yup yup'>
        """
        self._label.set_text(label)

    def get_label(self):
        """
        Return label text.
        >>> b = Button(u"Ok")
        >>> print(b.get_label())
        Ok
        >>> print(b.label)
        Ok
        """
        return self._label.text
    label = property(get_label)

    def keypress(self, size, key):
        if self._command_map[key] != ACTIVATE:
            return key

        self._emit('click')

    def mouse_event(self, size, event, button, x, y, focus):
        if button != 1 or not is_mouse_press(event):
            return False

        self._emit('click')
        return True