# WOD AI V11 - Kivy UI closer to the purple mockup
import os
import json
import math
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hexc
import certifi
from kivy.network.urlrequest import UrlRequest

# >>> حط رابط الـ Worker ديالك هنا (ماشي الـ key) <<<
WORKER_URL = 'PUT_WORKER_URL_HERE'

BG = '#07050f'
BG_TOP = '#2b0b66'
SURFACE = '#140d26'
SURFACE_2 = '#1d1236'
PURPLE = '#7b2fff'
PURPLE_LIGHT = '#c18bff'
WHITE = '#f7f2ff'
MUTED = '#a99db8'
BORDER = '#4a2c7a'

Window.clearcolor = hexc(BG)

# Put an Arabic-capable font here (e.g. NotoSansArabic-Regular.ttf) for Arabic text
FONT = 'fonts/NotoSansArabic-Regular.ttf'
FONT = FONT if os.path.exists(FONT) else 'Roboto'


def shape(value):
    value = str(value)
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(value))
    except Exception:
        return value


def gradient_texture(top, bottom):
    tex = Texture.create(size=(1, 2), colorfmt='rgba')
    b = [int(c * 255) for c in hexc(bottom)]
    t = [int(c * 255) for c in hexc(top)]
    tex.blit_buffer(bytes(b + t), colorfmt='rgba', bufferfmt='ubyte')
    tex.mag_filter = 'linear'
    return tex


class GScreen(Screen):
    """Screen with purple vertical gradient background."""
    def __init__(self, **kw):
        super().__init__(**kw)
        tex = gradient_texture(BG_TOP, BG)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(texture=tex, pos=self.pos, size=self.size)
        self.bind(pos=self._s, size=self._s)

    def _s(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size


class Box(BoxLayout):
    def __init__(self, color=SURFACE, radius=18, outline=True, alpha=0.9,
                 texture=None, **kw):
        super().__init__(**kw)
        self._r = dp(radius)
        self._outline = outline
        with self.canvas.before:
            Color(*hexc(color)[:3], alpha)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[self._r], texture=texture)
            if outline:
                Color(*hexc(BORDER))
                self._ln = Line(rounded_rectangle=(0, 0, 1, 1, self._r), width=1)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size
        if self._outline:
            self._ln.rounded_rectangle = (self.x, self.y, self.width,
                                          self.height, self._r)


class Txt(Label):
    def __init__(self, text='', color=WHITE, size=14, halign='left', **kw):
        super().__init__(**kw)
        self.font_name = FONT
        self.text = shape(text)
        self.color = hexc(color)
        self.font_size = sp(size)
        self.halign = halign
        self.valign = 'middle'
        self.bind(size=lambda *_: setattr(self, 'text_size', (self.width, self.height)))


class Pill(Button):
    """Rounded button with outline (filled or ghost)."""
    def __init__(self, text='', fill=None, radius=24, **kw):
        super().__init__(**kw)
        self.text = shape(text)
        self.font_name = FONT
        self.font_size = sp(13)
        self.background_normal = self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = hexc(WHITE)
        r = dp(radius)
        with self.canvas.before:
            Color(*(hexc(fill) if fill else (0.2, 0.1, 0.4, 0.35)))
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[r])
            Color(*hexc(PURPLE if not fill else PURPLE_LIGHT)[:3], 0.7)
            self._ln = Line(rounded_rectangle=(0, 0, 1, 1, r), width=1.1)
        self._r = r
        self.bind(pos=self._s, size=self._s)

    def _s(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size
        self._ln.rounded_rectangle = (self.x, self.y, self.width, self.height, self._r)


class Circle(Button):
    """Circular icon button."""
    def __init__(self, text='', fill=SURFACE_2, size_dp=42, glow=False, **kw):
        super().__init__(size_hint=(None, None), size=(dp(size_dp),) * 2, **kw)
        self.text = text
        self.background_normal = self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = hexc(WHITE)
        self.font_size = sp(16)
        with self.canvas.before:
            if glow:
                Color(*hexc(PURPLE)[:3], 0.35)
                self._g = Ellipse()
            Color(*hexc(fill)[:3], 0.9)
            self._bg = Ellipse()
            Color(*hexc(PURPLE)[:3], 0.9)
            self._ln = Line(width=1.2)
        self._glow = glow
        self.bind(pos=self._s, size=self._s)

    def _s(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size
        self._ln.ellipse = (self.x, self.y, self.width, self.height)
        if self._glow:
            self._g.pos = (self.x - dp(6), self.y - dp(6))
            self._g.size = (self.width + dp(12), self.height + dp(12))


class Orb(Widget):
    """Glowing purple orb. Set animate=True for pulsing."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.t = 0
        self._ev = None
        self.bind(pos=self.draw, size=self.draw)

    def start(self):
        if not self._ev:
            self._ev = Clock.schedule_interval(self._tick, 1 / 30)

    def stop(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None

    def _tick(self, dt):
        self.t += dt
        self.draw()

    def draw(self, *_):
        self.canvas.clear()
        cx, cy = self.center
        base = min(self.width, self.height) / 2
        pulse = 1 + 0.04 * math.sin(self.t * 3)
        with self.canvas:
            for i in range(10):  # soft glow
                r = base * pulse * (1.0 - i * 0.04)
                Color(0.5, 0.15, 1, 0.07 + i * 0.012)
                Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            for k in range(5):  # swirling rings
                a = self.t * (0.8 + k * 0.3) + k
                rx = base * 0.8 * pulse
                ry = rx * (0.45 + 0.1 * k)
                Color(0.75, 0.45, 1, 0.55)
                Line(ellipse=(cx - rx, cy - ry, 2 * rx, 2 * ry,
                              math.degrees(a) % 360, (math.degrees(a) + 250) % 360 + 360),
                     width=1.1)
            r = base * 0.16 * pulse  # bright core
            Color(1, 0.9, 1, 0.95)
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))


def topbar(title, back=None, menu=True):
    row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
    if back:
        b = Circle('<')
        b.bind(on_release=lambda *_: App.get_running_app().go(back))
        row.add_widget(b)
    row.add_widget(Txt(title, size=17, halign='center' if back else 'left'))
    if menu:
        m = Circle('=')
        m.bind(on_release=lambda *_: App.get_running_app().go('settings'))
        row.add_widget(m)
    return row


class WODAI(App):
    def build(self):
        self.title = 'WOD AI'
        self.history_path = os.path.join(self.user_data_dir, 'wod_ai_history.json')
        self.history = self.load_history()
        sm = ScreenManager(transition=FadeTransition(duration=0.15))
        for s in (HomeScreen(name='home'), ChatScreen(name='chat'),
                  VoiceScreen(name='voice'), HistoryScreen(name='history'),
                  SettingsScreen(name='settings')):
            sm.add_widget(s)
        self.sm = sm
        Window.bind(on_keyboard=self.on_key)
        return sm

    def on_key(self, _w, key, *_):
        if key == 27:  # Android back button
            if self.sm.current != 'home':
                self.go('home')
                return True
        return False

    def load_history(self):
        try:
            with open(self.history_path, encoding='utf-8') as f:
                r = json.load(f)
                return r if isinstance(r, list) else []
        except Exception:
            return []

    def save_history(self):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_chat(self, q, a):
        self.history.append({'question': q, 'answer': a,
                             'time': datetime.now().strftime('%Y-%m-%d %H:%M')})
        self.save_history()

    def go(self, name, prompt=None):
        self.sm.current = name
        if name == 'history':
            self.sm.get_screen('history').refresh()
        if name == 'chat' and prompt:
            self.sm.get_screen('chat').input.text = prompt


class HomeScreen(GScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        # greeting row
        top = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        av = Orb(size_hint=(None, None), size=(dp(44), dp(44)))
        top.add_widget(av)
        col = BoxLayout(orientation='vertical')
        col.add_widget(Txt('Hi there', color=MUTED, size=11))
        col.add_widget(Txt('Jack Johnson', size=15))
        top.add_widget(col)
        m = Circle('=')
        m.bind(on_release=lambda *_: App.get_running_app().go('settings'))
        top.add_widget(m)
        root.add_widget(top)

        root.add_widget(Txt('Smart Help,\nInstantly for You', size=28,
                            size_hint_y=None, height=dp(90)))

        # tool cards: one tall + two stacked
        tools = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(210))
        tall = Box(orientation='vertical', padding=dp(12), color=PURPLE, alpha=0.45,
                   texture=gradient_texture('#b04bff', '#1a0a3a'))
        tall.add_widget(Widget())
        tall.add_widget(Txt('Generating\nVisual', size=14, size_hint_y=None, height=dp(44)))
        tall.add_widget(self._open(tall, 'Create a visual: '))
        tools.add_widget(tall)

        right = BoxLayout(orientation='vertical', spacing=dp(10))
        for t, p in (('Generate\nDocument', 'Draft a document about '),
                     ('Organizing\nMeeting', 'Plan a meeting agenda for ')):
            c = Box(orientation='vertical', padding=dp(12), color=SURFACE_2)
            c.add_widget(Widget())
            c.add_widget(Txt(t, size=13, size_hint_y=None, height=dp(40)))
            self._open(c, p)
            tap = Button(background_color=(0, 0, 0, 0), background_normal='',
                         pos_hint={'x': 0, 'y': 0})
            tap.bind(on_release=lambda _b, p=p: App.get_running_app().go('chat', p))
            c.bind(on_touch_up=lambda w, touch, p=p: (
                App.get_running_app().go('chat', p) if w.collide_point(*touch.pos) else None))
            right.add_widget(c)
        tools.add_widget(right)
        root.add_widget(tools)

        # recent chat
        hdr = BoxLayout(size_hint_y=None, height=dp(30))
        hdr.add_widget(Txt('Recent Chat', size=15))
        see = Button(text='See All', size_hint_x=None, width=dp(70), font_size=sp(11),
                     background_normal='', background_color=(0, 0, 0, 0),
                     color=hexc(MUTED))
        see.bind(on_release=lambda *_: App.get_running_app().go('history'))
        hdr.add_widget(see)
        root.add_widget(hdr)

        chips = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(96))
        for label, prompt in (('Generate AI Image', 'Generate an image of '),
                              ('Summarize This', 'Summarize this: '),
                              ('Build Quick Report', 'Build a quick report on '),
                              ('Ask Anything Now', '')):
            b = Pill(label, radius=16)
            b.font_size = sp(11)
            b.bind(on_release=lambda _b, p=prompt: App.get_running_app().go('chat', p))
            chips.add_widget(b)
        root.add_widget(chips)

        root.add_widget(Widget())

        # start new chat pill + voice
        bottom = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        start = Pill('Start New Chat   >', radius=26)
        start.bind(on_release=lambda *_: App.get_running_app().go('chat'))
        bottom.add_widget(start)
        mic = Circle('MIC', size_dp=50, glow=True)
        mic.font_size = sp(10)
        mic.bind(on_release=lambda *_: App.get_running_app().go('voice'))
        bottom.add_widget(mic)
        root.add_widget(bottom)
        self.add_widget(root)

    def _open(self, card, prompt):
        # small arrow label; the whole card is tappable via on_touch_up
        arrow = Txt('>', color=PURPLE_LIGHT, size=16, halign='right',
                    size_hint_y=None, height=dp(24))
        if prompt.startswith('Create a visual'):
            arrow.bind(on_touch_up=lambda w, t: App.get_running_app().go('chat', prompt)
                       if w.collide_point(*t.pos) else None)
            return arrow
        card.add_widget(arrow)
        return arrow


class Bubble(Box):
    def __init__(self, text, user=False, **kw):
        super().__init__(color=SURFACE_2 if not user else PURPLE,
                         alpha=0.85 if not user else 0.35,
                         size_hint=(None, None), padding=dp(11), **kw)
        self.width = Window.width * 0.72
        self.label = Txt(text, size=13, size_hint_y=None)
        self.label.text_size = (self.width - dp(22), None)
        self.label.bind(texture_size=self._fit)
        self.add_widget(self.label)

    def _fit(self, _w, ts):
        self.label.height = ts[1]
        self.height = ts[1] + dp(22)


class ChatScreen(GScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(10))
        self.convo = []
        root.add_widget(topbar('Chat Bot', back='home'))

        self.msgs = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(12))
        self.msgs.bind(minimum_height=self.msgs.setter('height'))
        self.scroll = ScrollView(do_scroll_x=False)
        self.scroll.add_widget(self.msgs)
        root.add_widget(self.scroll)
        self.add_msg('Hello! Ask your question in Arabic, English, French, or any language.')

        comp = Box(size_hint_y=None, height=dp(54), padding=(dp(6), dp(5)),
                   spacing=dp(6), radius=27)
        plus = Button(text='+', size_hint_x=None, width=dp(34), background_normal='',
                      background_color=(0, 0, 0, 0), color=hexc(PURPLE_LIGHT),
                      font_size=sp(20))
        self.input = TextInput(
            hint_text='Ask AI anything...', multiline=False, font_size=sp(14),
            font_name=FONT, background_normal='', background_active='',
            background_color=(0, 0, 0, 0), foreground_color=hexc(WHITE),
            hint_text_color=hexc(MUTED), cursor_color=hexc(PURPLE_LIGHT),
            padding=[dp(4), dp(14), dp(4), dp(8)])
        self.input.bind(on_text_validate=self.send)
        mic = Button(text='MIC', size_hint_x=None, width=dp(40), font_size=sp(9),
                     background_normal='', background_color=(0, 0, 0, 0),
                     color=hexc(PURPLE_LIGHT))
        mic.bind(on_release=lambda *_: App.get_running_app().go('voice'))
        send = Circle('>', fill=PURPLE, size_dp=42)
        send.bind(on_release=self.send)
        for w in (plus, self.input, mic, send):
            comp.add_widget(w)
        root.add_widget(comp)
        self.add_widget(root)

    def add_msg(self, text, user=False):
        row = BoxLayout(size_hint_y=None, spacing=dp(8))
        bub = Bubble(text, user)
        if user:
            row.add_widget(Widget())
            row.add_widget(bub)
        else:
            av = Orb(size_hint=(None, None), size=(dp(30), dp(30)))
            row.add_widget(av)
            row.add_widget(bub)
            row.add_widget(Widget())
        bub.bind(height=lambda _w, h: setattr(row, 'height', h))
        self.msgs.add_widget(row)
        Clock.schedule_once(lambda *_: setattr(self.scroll, 'scroll_y', 0), 0.1)
        return bub

    def send(self, *_):
        q = self.input.text.strip()
        if not q:
            return
        self.input.text = ''
        self.add_msg(q, True)
        self.convo.append({'role': 'user', 'parts': [{'text': q}]})
        bub = self.add_msg('...')

        def ok(_r, res):
            reply = res.get('reply', 'Error') if isinstance(res, dict) else 'Error'
            bub.label.text = shape(reply)
            self.convo.append({'role': 'model', 'parts': [{'text': reply}]})
            App.get_running_app().add_chat(q, reply)

        def fail(_r, err):
            bub.label.text = shape('Connection error. Check your internet.')
            self.convo.pop()

        UrlRequest(WORKER_URL, req_body=json.dumps({'contents': self.convo[-20:]}),
                   req_headers={'Content-Type': 'application/json'},
                   on_success=ok, on_failure=fail, on_error=fail,
                   ca_file=certifi.where(), timeout=60)
        self.input.focus = True


class VoiceScreen(GScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        root.add_widget(topbar('Voice Analysis', back='home'))
        root.add_widget(Txt('Listening...', color=MUTED, size=12, halign='center',
                            size_hint_y=None, height=dp(28)))
        self.orb = Orb(size_hint=(1, 0.5))
        root.add_widget(self.orb)
        root.add_widget(Txt('Generate high-quality images\ninstantly using voice commands\n'
                            '- smart, fast, and powered by advanced AI',
                            size=14, halign='center', color='#d9cdee',
                            size_hint_y=None, height=dp(90)))
        root.add_widget(Widget())
        ctr = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(30),
                        padding=(dp(30), 0))
        ctr.add_widget(Widget())
        ctr.add_widget(Circle('R', size_dp=44))
        ctr.add_widget(Circle('MIC', fill=PURPLE, size_dp=70, glow=True))
        close = Circle('X', size_dp=44)
        close.bind(on_release=lambda *_: App.get_running_app().go('home'))
        ctr.add_widget(close)
        ctr.add_widget(Widget())
        root.add_widget(ctr)
        self.add_widget(root)

    def on_enter(self, *_):
        self.orb.start()

    def on_leave(self, *_):
        self.orb.stop()


class HistoryScreen(GScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(10))
        root.add_widget(topbar('Chat History', back='home'))
        self.items = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8))
        self.items.bind(minimum_height=self.items.setter('height'))
        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(self.items)
        root.add_widget(sv)
        self.add_widget(root)

    def refresh(self):
        self.items.clear_widgets()
        h = App.get_running_app().history
        if not h:
            self.items.add_widget(Txt('No conversations yet.', color=MUTED,
                                      size_hint_y=None, height=dp(60)))
            ret
