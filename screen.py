import curses


class Screen(object):
    def __init__(self, filename=None):
        self.display = [0] * 32 * 64
        self.counter = 0
        self.filename = filename
        self.debug_info = {
            'pc': 0,
            'v': {},
            'stack': {},
            'index': 0,
            'sp': 0,
            'operand': 0,
            'sprite': 0,
            'str': ''
        }

        self.init_hud()

    def get_pixel(self, x_pos, y_pos):
        try:
            return self.display[y_pos * 64 + x_pos]
        except IndexError:
            return 0

    def draw_pixel(self, x_pos, y_pos, pixel):
        try:
            self.display[y_pos * 64 + x_pos] = pixel
        except:
            pass

    def init_hud(self):
        self.stdscr = curses.initscr()

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        if curses.has_colors():
            curses.start_color()

        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)

        self.stdscr.addstr('Chip8 Emulator', curses.A_REVERSE)
        self.stdscr.chgat(-1, curses.A_REVERSE)

        self.display_window = curses.newwin(34, 68, 3, 3)
        self.display_window.keypad(1)
        self.display_window.timeout(16)
        self.display_window.box()

        if self.filename:
            self.display_window.addstr(0, 2, self.filename)

        max_width = self.stdscr.getmaxyx()[1]
        self.debug_window = curses.newwin(34, max_width - 75, 3, 72)
        self.debug_window.timeout(16)
        self.debug_window.box()
        self.debug_window.addstr(0, 2, 'debug')

        self.update_debug_info()

    def update_debug_info(self, debug_info={}):
        # self.debug_window.clear()
        self.debug_window.box()
        self.debug_info.update(debug_info)
        self.debug_window.addstr(1, 2, 'PC: %s' % self.debug_info['pc'])

        line = 2
        count = 0
        for key, value in self.debug_info['v'].items():
            self.debug_window.addstr(line + count, 2, '%s: %s' % (key, value))
            count += 1

        line = 2
        count = 0
        for key, value in self.debug_info['stack'].items():
            self.debug_window.addstr(line + count, 20, '%s: %s' % (key, value))
            count += 1

        line = count + 2
        self.debug_window.addstr(
            line, 2, 'index: %s' % self.debug_info['index'])

        self.debug_window.addstr(line + 1, 2, 'sp: %s' %
                                 self.debug_info['sp'])

        self.debug_window.addstr(line + 2, 2, 'operand: %s' %
                                 self.debug_info['operand'])

        self.debug_window.addstr(line + 3, 2, 'sprite: %s' %
                                 self.debug_info['sprite'])

    def clear(self):
        self.display = [0] * 32 * 64

    def update(self, callback=None):
        self.counter += 1

        # self.display_window.box()
        # self.display_window.addstr(0, 0, '%s count' % (self.counter % 100))
        padding_y = 1
        padding_x = 2
        # for x_index, line in enumerate(self.display):
        #     for y_index, pixel in enumerate(line):
        #         self.display_window.addstr(
        #             padding + x_index, padding + 1 + y_index, '#' if pixel else ' ')

        for index in range(32 * 64):
            line = index // 64
            column = index % 64

            pixel = self.display[index]

            if pixel == 1:
                pair = curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE
            else:
                pair = curses.color_pair(1) | curses.A_BOLD
            self.display_window.addstr(
                padding_y + line, padding_x + column, ' ', pair)

        self.stdscr.refresh()
        self.display_window.refresh()
        self.debug_window.refresh()

        key = self.display_window.getch()
        if key == ord('q'):
            curses.endwin()
            exit(0)

        elif key == ord('c'):
            if callback:
                callback()
