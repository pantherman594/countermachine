from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.properties import (BooleanProperty)

class ButtonM(Button):
    inside = BooleanProperty(False)

    def __init__(self, **kwargs):
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(ButtonM, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        inside = self.collide_point(*self.to_widget(*pos)) and not self.disabled
        if inside:
            Window.set_system_cursor('hand')
        if self.inside == inside:
            return
        self.inside = inside
        if not inside:
            Window.set_system_cursor('arrow')
