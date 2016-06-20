#!/usr/bin/env python
import os
import sys
import time
import shlex
import struct
import platform
import subprocess

import pyglet
import cocos
from cocos.director import director
from cocos.audio.pygame.mixer import Sound
from cocos.audio.pygame import mixer
import colorama
colorama.init()

# support running from locations outside the bin directory assuming symbolic links aren't used
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
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

    def get_speaker(self):
        return self._speaker

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

    def wait(self, duration):
        time.sleep(duration)

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

    def mainloop(self, runtime):
        while True:
            if runtime.can_step() is False and self.state is ConsoleView.IDLE:
                break
            if self.state is ConsoleView.IDLE:
                command = runtime.step()
                command.execute()
            elif self.state is ConsoleView.WAIT_INPUT:
                while True:
                    char = getch()
                    if char == "d":
                        self.state = ConsoleView.IDLE
                        break
                    elif char == "s":
                        clear_screen()
                        sys.exit(0)
            self.update()

        clear_screen()
        print "End of file reached. Press any key to exit."
        getch()

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


class CocosUILayer(cocos.layer.ColorLayer):

    is_event_handler = True
    UI_COLOR = (200, 200, 200)
    UI_OPACITY = 200
    UI_HEIGHT = 150

    def __init__(self):
        super(CocosUILayer, self).__init__(0, 0, 0, 0, CocosView.WIDTH, CocosUILayer.UI_HEIGHT)
        self.color = CocosUILayer.UI_COLOR
        self.opacity = CocosUILayer.UI_OPACITY

    def advance_request(self):
        pass

    def on_key_release(self, key, _):
        if key < 255 and chr(key) == CocosView.ADVANCE_NEXT_KEY:
            self.advance_request()


class CocosView(object):

    DIALOGUE, GET_CHOICE, WAIT, WAIT_INPUT, IDLE = range(5)
    WIDTH = 800
    HEIGHT = 600
    TITLE = "NMFe Standalone Player"
    ACTOR_FONT_SIZE = 20
    DIALOGUE_FONT_SIZE = 16
    ADVANCE_NEXT_KEY = "n"
    FONT = "Sans Serif"
    DIALOGUE_DELAY = 0.035

    def __init__(self):
        self._actor_label = None
        self._dialogue_box = None
        self._scene = None
        self._audio = None
        self._background = None
        self._ui_layer = None
        self._image_layer = None
        self._menu = None
        self._choice = None
        self._delete_queue = []
        self._display_queue = []
        self._dialogue_dirty = False
        self._dialogue_buffer = []
        self._avatars = {}
        self._speaker = None
        self._state = CocosView.IDLE
        self._start_time = -1
        self._duration = -1
        self._update_speaker = False

    def display_dialogue(self, dialogue):
        self._state = CocosView.DIALOGUE
        self._dialogue_dirty = True
        self._dialogue_buffer = list(dialogue)

    def set_speaker(self, speaker):
        self._speaker = speaker
        self._update_speaker = True

    def get_speaker(self):
        return self._speaker

    def display_background(self, background_path, transition):
        if self._background is not None:
            self._delete_queue.append(self._background)
        image = pyglet.image.load(background_path)
        self._background = cocos.sprite.Sprite(image)
        self._background.position = (CocosView.WIDTH / 2, CocosView.HEIGHT / 2)
        self._display_queue.append((self._background, -1))

    def clear_background(self):
        self._delete_queue.append(self._background)
        self._background = None

    def play_audio(self, audio_path):
        if self._audio is not None:
            self.stop_audio()
        self._audio = Sound(audio_path)
        self._audio.play(-1)

    def stop_audio(self):
        if self._audio is not None:
            self._audio.stop()
            self._audio = None

    def display_avatar(self, avatar_path):
        old_position = None
        already_displaying = False
        if self._avatars.has_key(self.get_speaker()):
            already_displaying = True
            current_avatar = self._avatars[self.get_speaker()]
            old_position = current_avatar.position
            self.remove_avatar(self.get_speaker())
        image = pyglet.image.load(avatar_path)
        sprite = cocos.sprite.Sprite(image)
        if old_position:
            sprite.position = old_position
        else:
            sprite.position = (CocosView.WIDTH / 2, sprite.height / 2)
        self._avatars[self.get_speaker()] = sprite
        if already_displaying:
            self._display_queue.append((sprite, 0))

    def remove_avatar(self, avatar):
        self._delete_queue.append(self._avatars[avatar])
        del self._avatars[avatar]

    def set_avatar_position(self, avatar, position):
        sprite = self._avatars[avatar]
        if position == "left":
            sprite.position = (sprite.width / 2, sprite.height / 2)
        elif position == "center":
            sprite.position = (CocosView.WIDTH / 2, sprite.height / 2)
        elif position == "right":
            sprite.position = (CocosView.WIDTH - sprite.width / 2, sprite.height / 2)
        if sprite not in self._image_layer:
            self._display_queue.append((sprite, 0))

    def wait(self, duration):
        self._check_delete_queue()
        self._duration = duration
        self._start_time = time.time()
        self._state = CocosView.WAIT

    def restore_context(self, commands):
        self._check_delete_queue()
        self.clear_background()
        self.stop_audio()
        for command in commands:
            command.execute()

    def display_choices(self, choices):
        self._state = CocosView.GET_CHOICE
        self._refresh_menu()
        choice_items = []
        for index, text in enumerate(choices):
            # counting in NMF starts at one, not zero, so we have to add one
            # to make up the difference
            callback = lambda: self._set_choice(index + 1)
            choice_items.append(cocos.menu.MenuItem(text, callback))
        self._menu.create_menu(choice_items)
        self._show_menu()

    def get_selected_choice(self):
        return self._choice

    def mainloop(self, runtime):
        mixer.init()
        director.init(width=CocosView.WIDTH, height=CocosView.HEIGHT, caption=CocosView.TITLE)
        self._runtime = runtime
        self._init_interface()
        self._scene.schedule(self._update)
        self._scene.schedule_interval(self._render_dialogue, CocosView.DIALOGUE_DELAY)
        director.run(self._scene)

    def _update(self, _):
        if self._runtime.can_step() is False and self._state is CocosView.IDLE:
            pyglet.app.exit()
        elif self._state is CocosView.IDLE:
            command = self._runtime.step()
            command.execute()
        elif self._state is CocosView.WAIT:
            current_time = time.time()
            if current_time - self._start_time >= self._duration:
                self._state = CocosView.IDLE

    def _render_dialogue(self, _):
        if self._dialogue_dirty:
            self._dialogue_dirty = False
            self._dialogue_box.element.text = ""
        if self._state is CocosView.DIALOGUE:
            self._check_delete_queue()
            self._check_display_queue()
            if len(self._dialogue_buffer) == 0:
                self._state = CocosView.WAIT_INPUT
            else:
                self._dialogue_box.element.text += self._dialogue_buffer.pop(0)
            if self._update_speaker:
                if self._speaker is None:
                    self._actor_label.element.text = ""
                else:
                    self._actor_label.element.text = self._speaker
                    self._update_speaker = False

    def _advance_request(self):
        if self._state is not CocosView.GET_CHOICE:
            if len(self._dialogue_buffer) > 0:
                self._dialogue_box.element.text += ''.join(self._dialogue_buffer)
                self._dialogue_buffer = []
            else:
                self._state = CocosView.IDLE

    def _check_delete_queue(self):
        while self._delete_queue:
            sprite = self._delete_queue.pop(0)
            sprite.kill()

    def _check_display_queue(self):
        while self._display_queue:
            sprite, z_value = self._display_queue.pop(0)
            self._image_layer.add(sprite, z=z_value)

    def _refresh_menu(self):
        if self._menu is not None:
            self._menu.kill()
        self._menu = cocos.menu.Menu()
        self._menu.font_item["font_size"] = 16
        self._menu.font_item_selected["font_size"] = 24

    def _hide_menu(self):
        if self._menu in self._scene:
            self._menu.kill()

    def _show_menu(self):
        self._scene.add(self._menu)

    def _set_choice(self, choice_index):
        self._choice = choice_index
        self._hide_menu()
        self._state = CocosView.IDLE

    def _init_interface(self):
        self._scene = cocos.scene.Scene()
        self._image_layer = cocos.layer.Layer()
        self._scene.add(self._image_layer)
        self._ui_layer = CocosUILayer()
        self._ui_layer.advance_request = self._advance_request
        self._actor_label = cocos.text.Label(font_name=CocosView.FONT,
                                            font_size=CocosView.ACTOR_FONT_SIZE,
                                            anchor_x="left",
                                            color=(100, 100, 150, 255))
        self._actor_label.position = (20, 120)
        self._ui_layer.add(self._actor_label)
        self._dialogue_box = cocos.text.Label(font_name=CocosView.FONT,
                                             font_size=CocosView.DIALOGUE_FONT_SIZE,
                                             anchor_x="left",
                                             color=(50, 50, 50, 255),
                                             width=CocosView.WIDTH - 100,
                                             multiline=True)
        self._dialogue_box.position = (20, 80)
        self._ui_layer.add(self._dialogue_box)
        self._scene.add(self._ui_layer)

def main():
    if os.getenv("NO_COCOS"):
        view = ConsoleView()
    else:
        view = CocosView()
    runtime = panzee.nmfe.Runtime(view)
    if len(sys.argv) < 2:
        print "Usage: nmfe-player scene"
        sys.exit(1)

    try:
        runtime.read(sys.argv[1])
    except panzee.nmfe.ParseException as e:
        print "Parse error:", str(e)
        sys.exit(1)
    view.mainloop(runtime)


if __name__ == "__main__":
    main()
