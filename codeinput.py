from pygments import highlight

from kivy.uix.codeinput import CodeInput
from kivy.core.window import Window
from kivy.core.text.markup import MarkupLabel as Label
from kivy.cache import Cache
from kivy.properties import (NumericProperty, AliasProperty, BooleanProperty)
from kivy.utils import boundary
from kivy.graphics import Color, Rectangle

Cache_get = Cache.get
Cache_append = Cache.append

FL_IS_LINEBREAK = 0x01

class CodeInputM(CodeInput):
    line_num_size = NumericProperty(0)
    inside = BooleanProperty(False)

    def __init__(self, **kwargs):
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(CodeInputM, self).__init__(**kwargs)
        self.line_num_size = len(str(len(self._lines) + 10))

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

    def _update_num_lines(self):
        line_num_size = len(str(len(self._lines) + 10))
        if line_num_size != self.line_num_size:
            self.line_num_size = line_num_size
        self._trigger_refresh_text()

    def _set_line_text(self, line_num, text):
        # Set current line with other text than the default one.
        self._update_num_lines()
        self._lines_labels[line_num] = self._create_line_label(text, line_num=line_num)
        self._lines[line_num] = text

    def _refresh_text(self, text, *largs):
        # Refresh all the lines from a new text.
        # By using cache in internal functions, this method should be fast.
        mode = 'all'
        if len(largs) > 1:
            mode, start, finish, _lines, _lines_flags, len_lines = largs
            # start = max(0, start)
            cursor = None
        else:
            cursor = self.cursor_index()
            _lines, self._lines_flags = self._split_smart(text)
        _lines_labels = []
        _line_rects = []
        _create_label = self._create_line_label

        for line_num, x in enumerate(_lines):
            ln = line_num if mode == 'all' else line_num + start
            lbl = _create_label(x, line_num=ln)
            _lines_labels.append(lbl)
            _line_rects.append(Rectangle(size=lbl.size))

        if mode == 'all':
            self._lines_labels = _lines_labels
            self._lines_rects = _line_rects
            self._lines[:] = _lines
        elif mode == 'del':
            if finish > start:
                self._insert_lines(start,
                                   finish if start == finish else (finish + 1),
                                   len_lines, _lines_flags,
                                   _lines, _lines_labels, _line_rects)
        elif mode == 'insert':
            self._insert_lines(
                start,
                finish if (start == finish and not len_lines)
                else (finish + 1),
                len_lines, _lines_flags, _lines, _lines_labels,
                _line_rects)

        min_line_ht = self._label_cached.get_extents('_')[1]
        # with markup texture can be of height `1`
        self.line_height = max(_lines_labels[0].height, min_line_ht)
        # self.line_spacing = 2
        # now, if the text change, maybe the cursor is not at the same place as
        # before. so, try to set the cursor on the good place
        row = self.cursor_row
        self.cursor = self.get_cursor_from_index(self.cursor_index()
                                                 if cursor is None else cursor)
        # if we back to a new line, reset the scroll, otherwise, the effect is
        # ugly
        if self.cursor_row != row:
            self.scroll_x = 0
        # with the new text don't forget to update graphics again
        self._trigger_update_graphics()

    def _get_line_options(self):
        kw = super(CodeInputM, self)._get_line_options()
        kw['linenumsize'] = self.line_num_size
        return kw

    def get_cursor_from_xy(self, x, y):
        '''Return the (col, row) of the cursor from an (x, y) position.
        '''
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        l = self._lines
        dy = self.line_height + self.line_spacing
        cx = x - self.x
        scrl_y = self.scroll_y
        scrl_x = self.scroll_x
        scrl_y = scrl_y / dy if scrl_y > 0 else 0
        cy = (self.top - padding_top + scrl_y * dy) - y
        cy = int(boundary(round(cy / dy - 0.5), 0, len(l) - 1))
        _get_text_width = self._get_text_width
        _tab_width = self.tab_width
        _label_cached = self._label_cached
        # Offset for horizontal text alignment
        xoff = 0
        halign = self.halign
        base_dir = self.base_direction or self._resolved_base_dir
        auto_halign_r = halign == 'auto' and base_dir and 'rtl' in base_dir
        if halign == 'center':
            viewport_width = self.width - padding_left - self.padding[2]  # _r
            xoff = int((viewport_width - self._get_row_width(cy)) / 2)
        elif halign == 'right' or auto_halign_r:
            viewport_width = self.width - padding_left - self.padding[2]  # _r
            xoff = viewport_width - self._get_row_width(cy)
        for i in range(0, len(l[cy])):
            if xoff + _get_text_width(l[cy][:i], _tab_width, _label_cached) + \
                  (_get_text_width(l[cy][i], _tab_width, _label_cached) -\
                  _get_text_width('', _tab_width, _label_cached)) * 0.6 +\
                  padding_left > cx + scrl_x:
                cx = i
                break
        return cx, cy

    def _create_line_label(self, text, hint=False, line_num=-1):
        # Create a label from a text, using line options
        ntext = text.replace(u'\n', u'').replace(u'\t', u' ' * self.tab_width)
        if line_num > -1:
            ntext = str(line_num + 1).rjust(self.line_num_size, ' ') + ' ' + ntext
        else:
            ntext = ' ' * (self.line_num_size + 1) + ntext
        if self.password and not hint:  # Don't replace hint_text with *
            ntext = u'*' * len(ntext)
        ntext = self._get_bbcode(ntext)
        kw = self._get_line_options()
        cid = u'{}\0{}\0{}'.format(ntext, self.password, kw)
        texture = Cache_get('textinput.label', cid)

        if texture is None:
            # FIXME right now, we can't render very long line...
            # if we move on "VBO" version as fallback, we won't need to
            # do this.
            # try to find the maximum text we can handle
            label = Label(text=ntext, **kw)
            if text.find(u'\n') > 0:
                label.text = u''
            else:
                label.text = ntext
            label.refresh()

            # ok, we found it.
            texture = label.texture
            Cache_append('textinput.label', cid, texture, timeout=5)
            label.text = ''
        return texture

    def _get_bbcode(self, ntext):
        # get bbcoded text for python
        try:
            ntext[0]
            # replace brackets with special chars that aren't highlighted
            # by pygment. can't use &bl; ... cause & is highlighted
            ntext = ntext.replace(u'[', u'\x01').replace(u']', u'\x02')
            ntext = highlight(ntext, self.lexer, self.formatter)
            ntext = ntext.replace(u'\x01', u'&bl;').replace(u'\x02', u'&br;')
            # replace special chars with &bl; and &br;
            ntext = ''.join((u'[color=', str(self.text_color), u']',
                             ntext, u'[/color]'))
            ntext = ntext.replace(u'\n', u'')
            # remove possible extra highlight options
            # ntext = ntext.replace(u'[u]', '').replace(u'[/u]', '')
            return ntext
        except IndexError:
            return ''

    def cursor_offset(self, r=-1, c=-1):
        '''Get the cursor x offset on the current line.
        '''
        offset = 0
        if r == -1:
            row = int(self.cursor_row)
        else:
            row = int(r)
        if c == -1:
            col = int(self.cursor_col)
        else:
            col = int(c)
        _lines = self._lines
        if not col:
            offset = self._get_text_width(
                '',
                self.tab_width,
                self._label_cached
            )
        elif row < len(_lines):
            offset = self._get_text_width(
                _lines[row][:col],
                self.tab_width,
                self._label_cached
            )
        return offset

    # override _split_smart to not split even in multiline
    def _split_smart(self, text):
        lines = text.split(u'\n')
        lines_flags = [0] + [FL_IS_LINEBREAK] * (len(lines) - 1)
        return lines, lines_flags

    def _get_cursor(self):
        return self._cursor

    def _set_cursor(self, pos):
        if not self._lines:
            self._trigger_refresh_text()
            return
        l = self._lines
        cr = boundary(pos[1], 0, len(l) - 1)
        cc = boundary(pos[0], 0, len(l[cr]))
        cursor = cc, cr

        # adjust scrollview to ensure that the cursor will be always inside our
        # viewport.
        padding_left = self.padding[0]
        padding_right = self.padding[2]
        viewport_width = self.width - padding_left - padding_right
        sx = self.scroll_x
        offset = self.cursor_offset(c=cc, r=cr)

        # if offset is outside the current bounds, readjust
        if offset > viewport_width + sx:
            self.scroll_x = offset - viewport_width
        if offset < sx:
            self.scroll_x = offset
        if offset < viewport_width * 0.25:
            self.scroll_x = 0

        # do the same for Y
        # this algo try to center the cursor as much as possible
        dy = self.line_height + self.line_spacing
        offsety = cr * dy
        sy = self.scroll_y
        padding_top = self.padding[1]
        padding_bottom = self.padding[3]
        viewport_height = self.height - padding_top - padding_bottom - dy
        if offsety > viewport_height + sy:
            sy = offsety - viewport_height
        if offsety < sy:
            sy = offsety
        self.scroll_y = sy

        if self._cursor == cursor:
            return

        self._cursor = cursor
        return True

    cursor = AliasProperty(_get_cursor, _set_cursor)
