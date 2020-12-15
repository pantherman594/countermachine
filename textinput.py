from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.properties import (BooleanProperty)

class TextInputM(TextInput):
    inside = BooleanProperty(False)

    def __init__(self, **kwargs):
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(TextInputM, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        inside = self.collide_point(*self.to_widget(*pos))
        if inside:
            Window.set_system_cursor('ibeam')
        if self.inside == inside:
            return
        self.inside = inside
        if not inside:
            Window.set_system_cursor('arrow')
