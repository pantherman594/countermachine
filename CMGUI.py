from functools import partial
import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.properties import (ListProperty, StringProperty, ObjectProperty, BooleanProperty, ListProperty, ReferenceListProperty)
from string import ascii_lowercase as lower

import countermachine_david as cm
import os

COLOR = [0, 0, 1, 1]
HIGHLIGHT = [1, 1, 0, 1]
TRANSPARENT = [0, 0, 0, 0]

class MainWindow(Widget):

    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    filename = StringProperty('')
    flowchart_state = BooleanProperty(False)
    counter_tape_state = BooleanProperty(False)
    counter_list = ListProperty([0]*26)

    wrapper = ScrollView()
    counter_tape_wrapper = BoxLayout()

    # Draws flowchart
    def draw_flowchart(self, filename):

        if self.flowchart_state:
            self.clear_flowchart()

        self.wrapper = ScrollView(do_scroll_y=True)

        assembled = cm.assemble_from_file(filename)[0]
        print(assembled)
        components = diagram(assembled)

        # Assign the number of column, spacing and padding
        root = GridLayout(size_hint_y=None, cols=3, padding=25, spacing=3, row_default_height='40dp',
                          row_force_default=True)
        root.bind(minimum_height=root.setter('height'))

        for component in components:
            if component is None:
                root.add_widget(Blank())
                continue

            widget, args, line = component

            component = widget(**args)

            root.add_widget(component)

        self.wrapper.add_widget(root)

        self.ids.flowchart.add_widget(self.wrapper)
        self.flowchart_state = True
        return

    def clear_flowchart(self):
        if self.flowchart_state:
            self.ids.flowchart.remove_widget(self.wrapper)
            self.flowchart_state = False
        return



    def on_text(self, value):
        try:
            l = value.split(',')
            for item in range(len(l)):
                self.counter_list[item] = int(l[item])
            self.draw_counter_tape()
        except:
            print('Cannot update counter tape')
        return

    def draw_counter_tape(self):
        if self.counter_tape_state:
            self.clear_counter_tape()

        self.counter_tape_wrapper = BoxLayout(orientation = "horizontal")

        for number in range(len(self.counter_list)):
            self.counter_tape_wrapper.add_widget(Label(text=str(self.counter_list[number])))

        self.ids.counter_tape.add_widget(self.counter_tape_wrapper)

        self.counter_tape_state = True

    def clear_counter_tape(self):
        if self.counter_tape_state:
            self.ids.counter_tape.remove_widget(self.counter_tape_wrapper)
            self.counter_tape_state = False



    def file_chooser(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.4, 0.7))
        self._popup.open()

    def file_saver(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content, size_hint=(0.4, 0.7))
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

    def save(self, path, filename):
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write(self.text_input.text)

        self.draw_flowchart(filename)
        self.filename = filename
        self.dismiss_popup()

    def load(self, path, filename):
        with open(os.path.join(path, filename[0])) as stream:
            self.text_input.text = stream.read()

        self.draw_flowchart(filename[0])
        self.filename = filename[0]
        self.dismiss_popup()



    def run_counter_program(self):
        if self.filename == '':
            # TODO: throw up an error popup later
            return
        self.counter_list = cm.runcp(self.filename, *self.counter_list)
        self.draw_counter_tape()
        return

    def __init__(self):
        super(MainWindow, self).__init__()
        self.draw_counter_tape()

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class Component(Widget):
    line_color = ListProperty(COLOR)
    label = StringProperty()

    def __init__(self, **kwargs):
        super(Component, self).__init__(**kwargs)

class HorizontalLine(Component):
    pass

class VerticalLine(Component):
    pass

class UpArrow(Component):
    pass

class DownArrow(Component):
    pass

class LeftArrow(Component):
    pass

class RightArrow(Component):
    pass

class Blank(Component):
    def __init__(self, label='', **kwargs):
        super(Blank, self).__init__(**kwargs)
        self.label = label

class Conditional(Component):
    def __init__(self, label='', **kwargs):
        super(Conditional, self).__init__(**kwargs)
        self.label = label

class Statement(Component):
    def __init__(self, label='', **kwargs):
        super(Statement, self).__init__(**kwargs)
        self.label = label

class Connector(Component):
    line_n = False
    line_s = False
    line_e = False
    line_w = False

    arrow_n = False
    arrow_s = False
    arrow_e = False
    arrow_w = False

    def __init__(self, label='', **kwargs):
        self.label = label

        for direction in 'nsew':
            for key in ['arrow_' + direction, 'line_' + direction]:
                setattr(self, key, kwargs.pop(key, False))

        super(Connector, self).__init__(**kwargs)

# Create the App class 
class CMGUIApp(App):
    def __init__(self):
        super(CMGUIApp, self).__init__()

    def build(self):
        #self.gui.ids.flowchart.add_widget(self.draw_flowchart('pow.cp'))

        return MainWindow()

def add_attributes_or_create_connector(line, index, attributes):
    connector = line[index]
    if connector is not None and connector[0] == Connector:
        connector[1].update(attributes)
    else:
        line[index] = [Connector, attributes, -1]

def diagram(program):
    components = []
    for i in range(len(program) * 2):
        components.append([None, None, None])

    components[0] = [None, [Connector, { 'line_n': True, 'line_s': True, 'arrow_s': True }, 0], None]

    for i, line in enumerate(program):
        if line[0] == 'B' and line[1] in lower:
            components[i*2+1][1] = [Conditional, { 'label': str(i) + ': ' + line[1] + '=0?' }, i]

            add_attributes_or_create_connector(components[i*2+2],
                                               1,
                                               { 'label': 'no', 'line_n': True, 'line_s': True, 'arrow_s': 'True' })

            start = i
            end = int(line[2:])

            if start < end:
                add_attributes_or_create_connector(components[i*2+1],
                                                   2,
                                                   { 'label': 'yes, goto ' + str(end), 'line_s': True, 'line_w': True })

                for j in range(start*2+2, end*2):
                    add_attributes_or_create_connector(components[j],
                                                       2,
                                                       { 'line_n': True, 'line_s': True })

                final = components[end*2]
                add_attributes_or_create_connector(final,
                                                   1,
                                                   { 'line_e': True, 'line_s': True, 'arrow_s': True })
                add_attributes_or_create_connector(final,
                                                   2,
                                                   { 'line_n': True, 'line_w': True })
            else:
                add_attributes_or_create_connector(components[i*2+1],
                                                   2,
                                                   { 'label': 'yes, goto ' + str(end), 'line_n': True, 'line_w': True })

                for j in range(end*2+1, start*2+1):
                    add_attributes_or_create_connector(components[j],
                                                       2,
                                                       { 'line_n': True, 'line_s': True })

                final = components[end*2]
                add_attributes_or_create_connector(final,
                                                   1,
                                                   { 'line_e': True, 'line_s': True, 'arrow_s': True })
                add_attributes_or_create_connector(final,
                                                   2,
                                                   { 'line_s': True, 'line_w': True })


        elif line[0] == 'B':
            components[i*2+1][1] = [Statement, { 'label': str(i) + ': goto ' + line[1:] }, i]

            start = i
            end = int(line[1:])

            if start < end:
                add_attributes_or_create_connector(components[i*2+1],
                                                   0,
                                                   { 'line_s': True, 'line_e': True })

                for j in range(start*2+2, end*2):
                    add_attributes_or_create_connector(components[j],
                                                       0,
                                                       { 'line_n': True, 'line_s': True })

                final = components[end*2]
                add_attributes_or_create_connector(final,
                                                   1,
                                                   { 'line_w': True, 'line_s': True, 'arrow_s': True })
                add_attributes_or_create_connector(final,
                                                   0,
                                                   { 'line_n': True, 'line_e': True })
            else:
                add_attributes_or_create_connector(components[i*2+1],
                                                   0,
                                                   { 'line_n': True, 'line_e': True })

                for j in range(end*2+1, start*2+1):
                    add_attributes_or_create_connector(components[j],
                                                       0,
                                                       { 'line_n': True, 'line_s': True })

                final = components[end*2]
                add_attributes_or_create_connector(final,
                                                   1,
                                                   { 'line_w': True, 'line_s': True, 'arrow_s': True })
                add_attributes_or_create_connector(final,
                                                   0,
                                                   { 'line_s': True, 'line_e': True })

        elif line[0] == 'I':
            components[i*2+1][1] = [Statement, { 'label': str(i) + ': inc ' + line[1] }, i]
            add_attributes_or_create_connector(components[i*2+2],
                                               1,
                                               { 'line_n': True, 'line_s': True, 'arrow_s': 'True' })

        elif line[0] == 'D':
            components[i*2+1][1] = [Statement, { 'label': str(i) + ': dec ' + line[1] }, i]
            add_attributes_or_create_connector(components[i*2+2],
                                               1,
                                               { 'line_n': True, 'line_s': True, 'arrow_s': 'True' })

        elif line[0] == 'P':
            components[i*2+1][1] = [Statement, { 'label': str(i) + ': print' }, i]
            add_attributes_or_create_connector(components[i*2+2],
                                               1,
                                               { 'line_n': True, 'line_s': True, 'arrow_s': 'True' })

        elif line[0] == 'M':
            file, macro_counters = line[1:].split('#')

            components[i*2+1][1] = [Statement, { 'label': str(i) + ': MACRO ' + file + ' ' + ' '.join(list(macro_counters)) }, i]
            add_attributes_or_create_connector(components[i*2+2],
                                               1,
                                               { 'line_n': True, 'line_s': True, 'arrow_s': 'True' })

        elif line[0] == 'H':
            components[i*2+1] = [
                None,
                [Statement, { 'label': str(i) + ': halt' }, i],
                None
            ]

    components_flattened = []
    for component_row in components:
        for component in component_row:
            components_flattened.append(component)

    return components_flattened

if __name__ == '__main__':
    Window.size = (1600, 900)
    CMGUIApp().run()
