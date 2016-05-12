import os
import sys
import time
import shlex
import struct
import platform
import subprocess

import colorama
colorama.init()

sys.path.append(os.pardir)
sys.path.append(os.curdir)
import panzee.nmfe


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen.
    Taken from http://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user"""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()


# taken from https://gist.github.com/jtriley/1108174
def get_terminal_size():
    """ getTerminalSize()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     originally retrieved from:
     http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    """
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            # needed for window's python in cygwin's xterm!
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None:
        tuple_xy = (80, 25)      # default value
    return tuple_xy


def _get_terminal_size_windows():
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except:
        pass


def _get_terminal_size_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return (cols, rows)
    except:
        pass


def _get_terminal_size_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack('hh',
                               fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            return cr
        except:
            pass
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])


def clear_screen():
    if sys.platform == "nt":
        _ = os.system("cls")
    else:
        _ = os.system("clear")


class ConsoleView(object):

    DIALOGUE, DRAW_CHOICE, WAIT_INPUT, IDLE = range(4)
    ACTOR_COLOR = colorama.Fore.BLUE
    DIALOGUE_COLOR = colorama.Fore.WHITE
    DIALOGUE_DELAY = 0.05
    CHOICE_COLOR = colorama.Fore.RED
    HELP_COLOR = colorama.Fore.GREEN
    HELP_STR = "d = next, s = exit, 1/2/3/etc. used for choice selection"

    def __init__(self):
        self.state = ConsoleView.IDLE
        self._dialogue_buffer = ""
        self._need_refresh = True
        self._speaker = None
        self._speaker_drawn = False
        self._choices = []

    def display_background(self, _, __):
        pass

    def clear_background(self):
        pass

    def play_audio(self, _):
        pass

    def stop_audio(self):
        pass

    def set_speaker(self, speaker):
        self._speaker = speaker

    def display_dialogue(self, dialogue):
        self.state = ConsoleView.DIALOGUE
        self._dialogue_buffer = list(dialogue)

    def display_choices(self, choices):
        self._choices = choices
        self.state = ConsoleView.DRAW_CHOICE

    def get_selected_choice(self):
        choice = int(getch())
        self._need_refresh = True
        self.state = ConsoleView.IDLE
        return choice

    def update(self):
        if self._need_refresh is True:
            self._draw_interface()
            self._need_refresh = False
        if self.state is ConsoleView.DIALOGUE:
            self._draw_speaker()
            self._draw_dialogue()
        elif self.state is ConsoleView.DRAW_CHOICE:
            self._draw_choices()

    def restore_context(self, commands):
        self.clear_background()
        self.stop_audio()
        for command in commands:
            command.execute()

    def _draw_interface(self):
        clear_screen()
        print ConsoleView.HELP_COLOR + ConsoleView.HELP_STR + colorama.Style.RESET_ALL
        _, height = get_terminal_size()
        print "\n" * (height - 6)

    def _draw_speaker(self):
        if self._speaker and self._speaker_drawn is False:
            print ConsoleView.ACTOR_COLOR + self._speaker + colorama.Style.RESET_ALL
        self._speaker_drawn = True

    def _draw_dialogue(self):
        next_char = self._dialogue_buffer.pop(0)
        sys.stdout.write(ConsoleView.DIALOGUE_COLOR + next_char + colorama.Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(ConsoleView.DIALOGUE_DELAY)
        if len(self._dialogue_buffer) < 1:
            self.state = ConsoleView.WAIT_INPUT
            self._need_refresh = True
            self._speaker_drawn = False
            return

    def _draw_choices(self):
        for index, choice in enumerate(self._choices):
            print "%s%d. %s%s" % (ConsoleView.CHOICE_COLOR, index + 1, choice, colorama.Style.RESET_ALL)
        self.state = ConsoleView.IDLE


def main():
    view = ConsoleView()
    runtime = panzee.nmfe.Runtime(view)
    if len(sys.argv) < 2:
        print "Usage: nmfe-player scene"
        sys.exit(1)

    try:
        runtime.read(sys.argv[1])
    except panzee.nmfe.ParseException as e:
        print "Parse error:", str(e)
        sys.exit(1)
    while True:
        if runtime.can_step() is False and view.state is ConsoleView.IDLE:
            break
        if view.state is ConsoleView.IDLE:
            try:
                command = runtime.step()
                command.execute()
            except IndexError:
                print runtime._index, len(runtime._commands)
                sys.exit(1)
        elif view.state is ConsoleView.WAIT_INPUT:
            while True:
                char = getch()
                if char == "d":
                    view.state = ConsoleView.IDLE
                    break
                elif char == "s":
                    clear_screen()
                    sys.exit(0)
        view.update()

    clear_screen()
    print "End of file reached. Press any key to exit."
    getch()


if __name__ == "__main__":
    main()
