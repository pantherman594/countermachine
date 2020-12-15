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
from kivy.properties import (ListProperty, StringProperty, ObjectProperty, BooleanProperty, ListProperty, ReferenceListProperty, NumericProperty)
from kivy.clock import Clock
from kivy.utils import escape_markup
from string import ascii_lowercase as lower

from codeinput import CodeInputM
from textinput import TextInputM
from button import ButtonM
import countermachine_david as cm
import os
from pygments.style import Style
from pygments.lexer import RegexLexer, bygroups
from pygments.token import Token, Comment, Name, Keyword, Generic, Number, Operator, String

COLOR = [0, 0, 1, 1]
HIGHLIGHT = [1, 1, 0, 1]
TRANSPARENT = [0, 0, 0, 0]

class GruvboxStyle(Style):
    """ Retro groove color scheme for Vim by Github: @morhetz """
    """ Adapted for Pygments by @daveyarwood """

    background_color = '#282828'
    styles = {
        Comment.Preproc:    'noinherit #8ec07c',
        Comment:            '#928374 italic',
        Generic.Deleted:    'noinherit #282828 bg:#fb4934',
        Generic.Emph:       '#83a598 underline',
        Generic.Error:      '#cc241d underline',
        Generic.Heading:    '#b8bb26 bold',
        Generic.Inserted:   'noinherit #282828 bg:#b8bb26',
        Generic.Output:     'noinherit #504945',
        Generic.Prompt:     '#ebdbb2',
        Generic.Strong:     '#ebdbb2',
        Generic.Subheading: '#b8bb26 bold',
        Generic.Traceback:  'bg:#fb4934 bold',
        Generic:            '#ebdbb2',
        Keyword.Type:       'noinherit #fabd2f',
        Keyword:            'noinherit #8ec07c',
        Name.Attribute:     '#b8bb26 bold',
        Name.Builtin:       '#fabd2f',
        Name.Constant:      'noinherit #d3869b',
        Name.Entity:        'noinherit #fabd2f',
        Name.Exception:     'noinherit #fb4934',
        Name.Function:      '#fabd2f',
        Name.Label:         'noinherit #fb4934',
        Name.Tag:           'noinherit #fb4934',
        Name.Variable:      'noinherit #ebdbb2',
        Name:               '#ebdbb2',
        Number.Float:       'noinherit #d3869b',
        Number:             'noinherit #d3869b',
        Operator:           '#fe8019',
        String.Symbol:      '#83a598',
        String:             'noinherit #b8bb26',
        Token:              'noinherit #665c54',
    }

class CPLexer(RegexLexer):
    name = 'CP'
    aliases = ['cp']
    filenames = ['*.cp']

    tokens = {
        'root': [
            (r'^ *[0-9]* ', Token),
            (r'#.*\n', Comment),
            (r'([a-zA-Z0-9_]+)(:)', bygroups(Generic.Heading, Generic)),
            (r'halt', Name.Tag),
            (r'(inc|dec)( )([a-z])', bygroups(Keyword.Type, Generic, Name.Variable)),
            (r'(goto)( )([a-zA-Z0-9_]+)( )(if)( )([a-z])( *= *)(0)', bygroups(Name.Tag, Generic, Generic.Heading, Generic, Keyword, Generic, Name.Variable, Generic, Number)),
            (r'(goto)( )([a-zA-Z0-9_]+)', bygroups(Name.Tag, Generic, Generic.Heading)),
            (r'(MACRO)( )([a-zA-Z0-9_]+)(( *[a-z])*)', bygroups(Name.Tag, Generic, Generic.Heading, Name.Variable)),
            (r'print', Name.Tag),
            (r' *#.*\n', Comment),
            (r'.*\n', Generic.Error),
        ]
    }

class MainWindow(Widget):

    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    tape_input = ObjectProperty(None)
    filename = StringProperty('')
    flowchart_state = BooleanProperty(False)
    counter_list = ListProperty([0]*26)
    counter_list_str = ListProperty(["0"]*26)
    counter_list_len = ListProperty([1]*26)
    counter_list_len_soft = ListProperty([1]*26)
    counter_list_total_len = NumericProperty(26)
    counter_list_total_len_soft = NumericProperty(26)
    assembled_counter_program = ObjectProperty(None)
    counter_program_generator = ObjectProperty(None)
    counter_program_step = NumericProperty(0)
    counter_program_step_count = NumericProperty(0)
    counter_program_history = ListProperty([])
    step_state = BooleanProperty(False)
    running = BooleanProperty(False)
    counter_clock = ObjectProperty(None)
    line_map = ObjectProperty(None)
    counter_delay = NumericProperty(0.1)

    CPLexer = CPLexer
    GruvboxStyle = GruvboxStyle

    wrapper = ScrollView()

    # Draws flowchart
    def draw_flowchart(self):
        if not self.assembled_counter_program:
            return

        if self.flowchart_state:
            self.clear_flowchart()

        self.wrapper = ScrollView(do_scroll_y=True)

        components = diagram(self.assembled_counter_program[0])

        # Assign the number of column, spacing and padding
        root = GridLayout(size_hint_y=None, cols=3, padding=25, spacing=3, row_default_height='40dp',
                          row_force_default=True)
        root.bind(minimum_height=root.setter('height'))

        line_map = dict()

        for component in components:
            if component is None:
                root.add_widget(Blank())
                continue

            widget, args, line = component
            component = widget(**args)
            component.bind(on_touch_up=partial(self.on_component_press, line))
            root.add_widget(component)

            if line != -1:
                if line not in line_map:
                    line_map[line] = []
                line_map[line].append(component)

        self.wrapper.add_widget(root)

        self.ids.flowchart.add_widget(self.wrapper)

        self.flowchart_state = True
        self.line_map = line_map

        self.reset_generator()

        return

    def on_component_press(self, line, instance, ev):
        if line == -1:
            return False

        if not instance.collide_point(*ev.pos):
            return False

        file_line = self.assembled_counter_program[2][line]
        newlines = [i for i, n in enumerate(self.text_input.text) if n == '\n']

        try:
            start_index = newlines[file_line - 1]
        except IndexError:
            start_index = 0
        try:
            end_index = newlines[file_line]
        except IndexError:
            end_index = len(self.text_input.text)

        self.text_input.focus = True
        Clock.schedule_once(lambda dt: self.text_input.select_text(start_index, end_index))
        return True

    def reset_all(self):
        if self.counter_clock is not None:
            self.counter_clock.cancel()
        self.running = False
        self.on_text(self.tape_input.text)

    def reset_generator(self):
        if not self.assembled_counter_program:
            self.step_state = False
            self.running = False
            self.counter_program_step = 0
            return

        if self.counter_program_step in self.line_map:
            for component in self.line_map[self.counter_program_step]:
                component.line_color = COLOR

        if 0 in self.line_map:
            for component in self.line_map[0]:
                component.line_color = HIGHLIGHT

        self.counter_program_step = 0
        self.counter_program_step_count = 0
        self.counter_program_history = [(self.counter_list, 0)]

        self.counter_program_generator = cm.interpret_generator(self.assembled_counter_program,
                                                                *self.counter_list)

        self.step_state = True

    def step_counter_program(self):
        if self.flowchart_state and self.step_state:
            if self.counter_program_step in self.line_map:
                for component in self.line_map[self.counter_program_step]:
                    component.line_color = COLOR

            self.counter_program_step_count += 1
            step_count = self.counter_program_step_count
            try:
                next_step = self.counter_program_history[step_count]
            except:
                next_step = next(self.counter_program_generator, None)
                if next_step is None:
                    self.counter_program_history.append(None)
                else:
                    self.counter_program_history.append((next_step[0][:], next_step[1]))

            if next_step is None:
                self.step_state = False

                if self.running:
                    self.running = False
                    self.counter_clock.cancel()

                return

            self.counter_list, self.counter_program_step = next_step
            self.update_counter_tape_strings()
            if self.counter_program_step in self.line_map:
                for component in self.line_map[self.counter_program_step]:
                    component.line_color = HIGHLIGHT

        else:
            self.running = False
            self.counter_clock.cancel()

    def update_counter_tape_strings(self):
        # prevent divide by 0 error
        self.counter_list_total_len = 1
        for number in range(26):
            self.counter_list_str[number] = str(self.counter_list[number])
            self.counter_list_len[number] = len(self.counter_list_str[number])
            self.counter_list_len_soft[number] = (self.counter_list_len[number] - 1) / 4 + 1
            self.counter_list_total_len += self.counter_list_len[number]
        self.counter_list_total_len -= 1
        self.counter_list_total_len_soft = 26 + ((self.counter_list_total_len - 26) / 4)
        print(self.counter_list_total_len_soft, self.counter_list_total_len)

    def clear_flowchart(self):
        if self.flowchart_state:
            self.ids.flowchart.remove_widget(self.wrapper)
            self.flowchart_state = False
            self.line_map = dict()
            self.counter_program_step = 0
        return

    def on_text(self, value):
        if self.running:
            return

        try:
            l = value.split(',')
            self.counter_list = [0]*26
            self.update_counter_tape_strings()
            for item in range(len(l)):
                self.counter_list[item] = int(l[item])
            self.update_counter_tape_strings()
        except:
            print('Cannot update counter tape')
        self.reset_generator()
        return

    def file_chooser(self):
        self.dismiss_popup()

        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.4, 0.7))
        self._popup.open()

    def file_saver(self):
        self.dismiss_popup()

        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content, size_hint=(0.4, 0.7))
        self._popup.open()

    def dismiss_popup(self):
        if hasattr(self, '_popup'):
            self._popup.dismiss()

    def reassemble_counter_program(self, filename):
        assembled = cm.assemble_from_file(filename)
        self.assembled_counter_program = assembled

    def save(self, path, filename):
        if len(filename) < 3 and filename[-3:] != '.cp':
            filename += '.cp'

        file = os.path.join(path, filename)

        with open(file, 'w') as stream:
            stream.write(self.text_input.text)

        self.filename = os.path.realpath(file)
        self.reassemble_counter_program(self.filename)
        try:
            self.draw_flowchart()
        except:
            print("failed to draw flowchart")
        self.dismiss_popup()

    def load(self, path, filename):
        if len(filename) < 1:
            return

        file = os.path.join(path, filename[0])
        with open(file) as stream:
            self.text_input.text = stream.read()

        self.filename = os.path.realpath(file)
        self.reassemble_counter_program(self.filename)
        try:
            self.draw_flowchart()
        except:
            print("failed to draw flowchart")
        self.dismiss_popup()

    def step_back_counter_program(self):
        self.step_state = True
        if self.counter_program_step in self.line_map:
            for component in self.line_map[self.counter_program_step]:
                component.line_color = COLOR

        self.counter_program_step_count -= 1
        next_step = self.counter_program_history[self.counter_program_step_count]
        self.counter_list, self.counter_program_step = next_step
        if self.counter_program_step in self.line_map:
            for component in self.line_map[self.counter_program_step]:
                component.line_color = HIGHLIGHT

        self.draw_counter_tape()

    def run_or_pause_counter_program(self):
        if self.running:
            self.running = False
            self.counter_clock.cancel()
        else:
            self.running = True
            if self.counter_delay != 0:
                self.counter_clock = Clock.schedule_interval(lambda dt: self.step_counter_program(), self.counter_delay)
            else:
                if self.counter_program_step in self.line_map:
                    for component in self.line_map[self.counter_program_step]:
                        component.line_color = COLOR

                for value in self.counter_program_generator:
                    self.counter_program_step_count += 1
                    new_value = (value[0][:], value[1])
                    try:
                        self.counter_program_history[self.counter_program_step_count] = new_value
                    except:
                        self.counter_program_history.append(new_value)

                self.counter_list, self.counter_program_step = self.counter_program_history[-1]

                self.step_state = False
                self.running = False

                self.update_counter_tape_strings()

    def update_delay(self, value):
        try:
            self.counter_delay = float(value)

            if self.running:
                # Recreate the clock with the new delay
                self.run_or_pause_counter_program()
                self.run_or_pause_counter_program()
        except:
            print('Invalid delay')

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        modifiers_no_caps = modifiers[:]
        if 'capslock' in modifiers_no_caps:
            modifiers_no_caps.remove('capslock')
        ctrl_modifiers = ['ctrl', 'lctrl', 'rctrl']
        ctrl = len(modifiers_no_caps) == 1 and modifiers_no_caps[0] in ctrl_modifiers

        if keycode[0] == 115 and ctrl: # s
            if self.filename:
                self.save('', self.filename)
            else:
                self.file_saver()
            return True
        if keycode[0] == 111 and ctrl: # o
            self.file_chooser()
            return True

        return False

    def _keyboard_closed(self):
        pass

    def __init__(self):
        super(MainWindow, self).__init__()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_key_down)
        self.update_counter_tape_strings()

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
        self.bind(on_start=self.post_build)

        return MainWindow()

    def post_build(self, ev):
        Window.bind(on_keyboard=self.key_handler)

    def key_handler(self, window, keycode1, keycode2, text, modifiers):
        if keycode1 == 27: # escape
            # Ignore the escape key so that it doesn't close the app
            return True
        return False


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

    components[0] = [None, [Connector, { 'line_n': True, 'line_s': True, 'arrow_s': True }, -1], None]

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
