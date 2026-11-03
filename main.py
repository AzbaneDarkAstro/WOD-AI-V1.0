# WOD AI V10 - improved mobile UI prototype
# English interface; chat accepts multilingual text.
# Real AI replies and live voice features require a secure backend/service.

import os
import json
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.utils import get_color_from_hex

BG = '#080610'
SURFACE = '#151020'
SURFACE_2 = '#211432'
PURPLE = '#873BFF'
PURPLE_LIGHT = '#C18BFF'
WHITE = '#F7F2FF'
MUTED = '#A99DB8'
BORDER = '#39264F'

Window.clearcolor = get_color_from_hex(BG)


def display_text(value):
    """Shape Arabic if optional packages are installed; preserve other scripts."""
    value = str(value)
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(value))
    except Exception:
        return value


class RoundedBox(BoxLayout):
    def __init__(self, color=SURFACE, radius=18, outline=False, **kwargs):
        super().__init__(**kwargs)
        self._rgba = get_color_from_hex(color)
        self._radius = dp(radius)
        self._outline = outline
        with self.canvas.before:
            Color(*self._rgba)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[self._radius])
            if outline:
                Color(*get_color_from_hex(BORDER))
                self._line = Line(rounded_rectangle=(self.x, self.y,
                    self.width, self.height, self._radius), width=1)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        if self._outline:
            self._line.rounded_rectangle = (self.x, self.y,
                self.width, self.height, self._radius)


class TextLabel(Label):
    def __init__(self, text='', color=WHITE, size=14, halign='left', **kwargs):
        super().__init__(**kwargs)
        self.text = display_text(text)
        self.color = get_color_from_hex(color)
        self.font_size = sp(size)
        self.halign = halign
        self.valign = 'middle'
        self.bind(size=self._sync_text)

    def _sync_text(self, *_):
        self.text_size = (self.width, None)


class PurpleButton(Button):
    def __init__(self, text='', fill=PURPLE, **kwargs):
        super().__init__(**kwargs)
        self.text = display_text(text)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = get_color_from_hex(WHITE)
        self.font_size = sp(13)
        self._fill = get_color_from_hex(fill)
        with self.canvas.before:
            Color(*self._fill)
            self._shape = RoundedRectangle(pos=self.pos, size=self.size,
                                           radius=[dp(14)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._shape.pos = self.pos
        self._shape.size = self.size


def header(title='WOD AI'):
    row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
    mark = RoundedBox(color=SURFACE_2, size_hint_x=None, width=dp(42),
                      padding=dp(4))
    mark.add_widget(TextLabel('W', color=PURPLE_LIGHT, size=22, halign='center'))
    row.add_widget(mark)
    name = TextLabel(title, size=20)
    name.bold = True
    row.add_widget(name)
    settings = PurpleButton('...', fill=SURFACE_2,
                            size_hint_x=None, width=dp(45))
    settings.bind(on_release=lambda *_: App.get_running_app().go('settings'))
    row.add_widget(settings)
    return row


def bottom_nav():
    nav = RoundedBox(orientation='horizontal', size_hint_y=None,
                     height=dp(59), padding=dp(4), spacing=dp(3), color=SURFACE)
    for label, target in [('HOME', 'home'), ('CHAT', 'chat'),
                          ('VOICE', 'voice'), ('HISTORY', 'history')]:
        b = Button(text=label, background_normal='',
                   background_color=(0, 0, 0, 0),
                   color=get_color_from_hex(PURPLE_LIGHT), font_size=sp(10))
        b.bind(on_release=lambda _b, t=target: App.get_running_app().go(t))
        nav.add_widget(b)
    return nav


class WODAI(App):
    def build(self):
        self.title = 'WOD AI'
        self.history_path = os.path.join(self.user_data_dir, 'wod_ai_history.json')
        self.history = self.load_history()
        manager = ScreenManager()
        for screen in (HomeScreen(name='home'), ChatScreen(name='chat'),
                       VoiceScreen(name='voice'), HistoryScreen(name='history'),
                       SettingsScreen(name='settings')):
            manager.add_widget(screen)
        self.manager = manager
        return manager

    def load_history(self):
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
                return result if isinstance(result, list) else []
        except Exception:
            return []

    def save_history(self):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_chat(self, question, answer):
        self.history.append({'question': question, 'answer': answer,
                             'time': datetime.now().strftime('%Y-%m-%d %H:%M')})
        self.save_history()

    def go(self, screen):
        self.manager.current = screen
        if screen == 'history':
            self.manager.get_screen('history').refresh()


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(10))
        root.add_widget(header())
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None,
                            spacing=dp(14), padding=(0, dp(3), 0, dp(12)))
        content.bind(minimum_height=content.setter('height'))

        hero = RoundedBox(orientation='vertical', color=SURFACE_2,
                          padding=dp(17), spacing=dp(7),
                          size_hint_y=None, height=dp(175), outline=True)
        hero.add_widget(TextLabel('WELCOME TO YOUR AI WORKSPACE',
                                  color=PURPLE_LIGHT, size=10))
        hero.add_widget(TextLabel('Smart Help,\nInstantly for You', size=25))
        hero.add_widget(TextLabel('One assistant. Many languages. Endless ideas.',
                                  color=MUTED, size=12))
        start = PurpleButton('START NEW CHAT', size_hint_y=None, height=dp(40))
        start.bind(on_release=lambda *_: App.get_running_app().go('chat'))
        hero.add_widget(start)
        content.add_widget(hero)

        content.add_widget(TextLabel('EXPLORE YOUR TOOLS', size=16))
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None,
                          row_default_height=dp(145), row_force_default=True)
        grid.bind(minimum_height=grid.setter('height'))
        tools = [
            ('01', 'Generate Visual', 'Create image ideas and visuals'),
            ('02', 'Generate Document', 'Draft and organize documents'),
            ('03', 'Organize Meeting', 'Plan agendas and notes'),
            ('04', 'Writing Assistant', 'Improve text and writing'),
            ('05', 'Idea Generator', 'Explore new possibilities'),
            ('06', 'Voice Analysis', 'Open voice assistant'),
        ]
        for number, title, subtitle in tools:
            tile = RoundedBox(orientation='vertical', color=SURFACE,
                              padding=dp(11), spacing=dp(5), outline=True)
            tile.add_widget(TextLabel(number, color=PURPLE_LIGHT, size=12))
            tile.add_widget(TextLabel(title, size=14))
            tile.add_widget(TextLabel(subtitle, color=MUTED, size=10))
            button = PurpleButton('OPEN', size_hint_y=None, height=dp(32))
            target = 'voice' if title == 'Voice Analysis' else 'chat'
            button.bind(on_release=lambda _b, t=target: App.get_running_app().go(t))
            tile.add_widget(button)
            grid.add_widget(tile)
        content.add_widget(grid)

        content.add_widget(TextLabel('RECENT ACTIVITY', size=16))
        recent = RoundedBox(orientation='vertical', color=SURFACE,
                            padding=dp(12), size_hint_y=None, height=dp(65))
        recent.add_widget(TextLabel('Your recent conversations appear here.',
                                    color=MUTED, size=11))
        content.add_widget(recent)
        scroll.add_widget(content)
        root.add_widget(scroll)
        root.add_widget(bottom_nav())
        self.add_widget(root)


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(9))
        root.add_widget(header('WOD AI  /  CHAT'))
        self.messages = BoxLayout(orientation='vertical', size_hint_y=None,
                                  spacing=dp(10), padding=dp(3))
        self.messages.bind(minimum_height=self.messages.setter('height'))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self.messages)
        self.scroll = scroll
        welcome = RoundedBox(size_hint_y=None, height=dp(78), padding=dp(11))
        welcome.add_widget(TextLabel(
            'Hello! Ask your question in Arabic, English, French, or another language.',
            size=13))
        self.messages.add_widget(welcome)
        root.add_widget(scroll)

        composer = RoundedBox(orientation='horizontal', size_hint_y=None,
                              height=dp(58), padding=dp(5), spacing=dp(7))
        self.input = TextInput(
            hint_text='Ask anything...', multiline=False, font_size=sp(14),
            background_normal='', background_active='',
            background_color=get_color_from_hex(SURFACE_2),
            foreground_color=get_color_from_hex(WHITE),
            hint_text_color=get_color_from_hex(MUTED),
            cursor_color=get_color_from_hex(PURPLE_LIGHT),
            padding=[dp(10), dp(15), dp(10), dp(8)])
        self.input.bind(on_text_validate=self.send)
        send = PurpleButton('SEND', size_hint_x=None, width=dp(67))
        send.bind(on_release=self.send)
        composer.add_widget(self.input)
        composer.add_widget(send)
        root.add_widget(composer)
        root.add_widget(bottom_nav())
        self.add_widget(root)

    def add_bubble(self, text, user=False):
        bubble = RoundedBox(orientation='vertical', size_hint=(0.94, None),
                            padding=dp(11), color=PURPLE if user else SURFACE,
                            outline=not user)
        label = TextLabel(text, size=13)
        label.size_hint_y = None
        label.text_size = (Window.width * 0.78, None)
        label.texture_update()
        label.height = max(dp(30), label.texture_size[1] + dp(10))
        bubble.add_widget(label)
        bubble.height = label.height + dp(22)
        self.messages.add_widget(bubble)
        self.scroll.scroll_y = 0

    def send(self, *_):
        question = self.input.text.strip()
        if not question:
            return
        self.input.text = ''
        self.add_bubble(question, True)
        answer = ('Your message was received. The AI service is not connected yet. '
                  'After secure backend setup, WOD AI will generate a real reply in the language you use.')
        self.add_bubble(answer)
        App.get_running_app().add_chat(question, answer)


class VoiceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(12))
        root.add_widget(header('VOICE ANALYSIS'))
        root.add_widget(TextLabel('LISTENING MODE', color=MUTED, size=11,
                                  halign='center', size_hint_y=None, height=dp(35)))
        visual = BoxLayout(orientation='vertical', spacing=dp(8))
        orb = BoxLayout(size_hint=(1, 0.75))
        from kivy.uix.widget import Widget
        glow = Widget()
        with glow.canvas:
            Color(0.35, 0.08, 0.85, 0.18)
            Ellipse(pos=(Window.width/2-dp(105), dp(260)), size=(dp(210), dp(210)))
            Color(0.58, 0.20, 1, 0.45)
            Line(circle=(Window.width/2, dp(365), dp(83)), width=2)
            Color(0.72, 0.35, 1, 0.85)
            Line(circle=(Window.width/2, dp(365), dp(62)), width=1.5)
            Color(0.85, 0.65, 1, 1)
            Ellipse(pos=(Window.width/2-dp(7), dp(358)), size=(dp(14), dp(14)))
        orb.add_widget(glow)
        visual.add_widget(orb)
        visual.add_widget(TextLabel('Your voice assistant', size=19, halign='center'))
        visual.add_widget(TextLabel('Microphone and speech recognition will be enabled in a later build.',
                                    color=MUTED, size=11, halign='center'))
        root.add_widget(visual)
        controls = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10))
        for label in ('RESET', 'MIC', 'CLOSE'):
            controls.add_widget(PurpleButton(label, fill=SURFACE_2 if label != 'MIC' else PURPLE))
        root.add_widget(controls)
        root.add_widget(bottom_nav())
        self.add_widget(root)


class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(10))
        self.root.add_widget(header('CHAT HISTORY'))
        self.items = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8))
        self.items.bind(minimum_height=self.items.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.items)
        self.root.add_widget(scroll)
        self.root.add_widget(bottom_nav())
        self.add_widget(self.root)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        self.items.clear_widgets()
        history = App.get_running_app().history
        if not history:
            self.items.add_widget(TextLabel('No conversations yet.', color=MUTED,
                                            size_hint_y=None, height=dp(60)))
            return
        for item in reversed(history[-40:]):
            card = RoundedBox(orientation='vertical', padding=dp(10),
                              size_hint_y=None, height=dp(72), outline=True)
            card.add_widget(TextLabel(item.get('question', ''), size=12))
            card.add_widget(TextLabel(item.get('time', ''), color=MUTED, size=10))
            self.items.add_widget(card)


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(11))
        root.add_widget(header('SETTINGS'))
        rows = [
            'Interface language: English',
            'Chat language: follows your message',
            'Theme: Midnight Purple',
            'Build: WOD AI V10',
            'AI connection: Not connected yet',
        ]
        for item in rows:
            card = RoundedBox(size_hint_y=None, height=dp(59), padding=dp(12), outline=True)
            card.add_widget(TextLabel(item, size=12))
            root.add_widget(card)
        root.add_widget(TextLabel(
            'Multilingual input is supported by the interface. Real AI responses require a secure online model connection.',
            color=MUTED, size=11))
        root.add_widget(bottom_nav())
        self.add_widget(root)


if __name__ == '__main__':
    WODAI().run()
