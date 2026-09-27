"""
Personal Assistant (starter core)
----------------------------------
A minimal, working foundation for your own "Jarvis"-style app.

What this version does:
- Simple chat interface (type a message, get a reply)
- Calls the Claude API for the "brain"
- Saves your API key locally on the device (Settings screen)
- Stores basic conversation memory in a local file

What it does NOT do yet:
- Voice input/output, wake word, floating widget, smart home control,
  self-upgrade, etc. Those are future plugins — add them one at a time
  by creating new files in the plugins/ folder and wiring them into
  on_send() below. This file is intentionally kept small so it's easy
  to understand and extend.
"""

import json
import os
import threading
import urllib.request

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread
from kivy.uix.popup import Popup

from plugins.voice import speak, VoiceListener
from plugins import plugin_loader
from plugins import self_upgrade

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
MEMORY_PATH = os.path.join(APP_DIR, "memory.json")

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5"  # change if you want a different model


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


class ChatBubble(Label):
    def __init__(self, text, **kwargs):
        super().__init__(
            text=text,
            size_hint_y=None,
            text_size=(None, None),
            halign="left",
            valign="top",
            padding=(10, 10),
            **kwargs
        )
        self.bind(texture_size=self._update_height)

    def _update_height(self, *args):
        self.height = self.texture_size[1] + 20


class AssistantRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.config_data = load_json(CONFIG_PATH, {"api_key": "", "speak_replies": True})
        self.memory = load_json(MEMORY_PATH, {"history": []})
        self.voice_listener = VoiceListener()
        plugin_loader.load_all()

        # --- Top bar ---
        top_bar = BoxLayout(size_hint_y=None, height=50)
        title = Label(text="My Assistant", bold=True)
        upgrade_btn = Button(text="Upgrade", size_hint_x=None, width=100)
        upgrade_btn.bind(on_press=self.open_upgrade)
        settings_btn = Button(text="Settings", size_hint_x=None, width=100)
        settings_btn.bind(on_press=self.open_settings)
        top_bar.add_widget(title)
        top_bar.add_widget(upgrade_btn)
        top_bar.add_widget(settings_btn)
        self.add_widget(top_bar)

        # --- Chat scroll area ---
        self.scroll = ScrollView()
        self.chat_log = BoxLayout(orientation="vertical", size_hint_y=None, spacing=8, padding=8)
        self.chat_log.bind(minimum_height=self.chat_log.setter("height"))
        self.scroll.add_widget(self.chat_log)
        self.add_widget(self.scroll)

        for turn in self.memory.get("history", [])[-20:]:
            self._add_bubble(f"{turn['role']}: {turn['content']}")

        # --- Input row ---
        input_row = BoxLayout(size_hint_y=None, height=50)
        self.text_input = TextInput(multiline=False)
        self.text_input.bind(on_text_validate=self.on_send)
        mic_btn = Button(text="🎤", size_hint_x=None, width=60)
        mic_btn.bind(on_press=self.on_mic_press)
        send_btn = Button(text="Send", size_hint_x=None, width=90)
        send_btn.bind(on_press=self.on_send)
        input_row.add_widget(self.text_input)
        input_row.add_widget(mic_btn)
        input_row.add_widget(send_btn)
        self.add_widget(input_row)

    def on_mic_press(self, *args):
        self._add_bubble("(listening...)")

        def on_result(text):
            # remove the "(listening...)" placeholder bubble
            if self.chat_log.children:
                self.chat_log.remove_widget(self.chat_log.children[0])
            self.text_input.text = text
            self.on_send()

        def on_error(msg):
            if self.chat_log.children:
                self.chat_log.remove_widget(self.chat_log.children[0])
            self._add_bubble(f"(voice error: {msg})")

        self.voice_listener.start(on_result, on_error)

    def _add_bubble(self, text):
        bubble = ChatBubble(text=text)
        self.chat_log.add_widget(bubble)

    def open_upgrade(self, *args):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        box.add_widget(Label(
            text="Describe the new feature in plain words:",
            size_hint_y=None, height=30
        ))
        desc_input = TextInput(hint_text="e.g. tell me a random joke when I say 'joke'", multiline=True)
        generate_btn = Button(text="Generate", size_hint_y=None, height=50)
        status_label = Label(text="", size_hint_y=None, height=30)
        box.add_widget(desc_input)
        box.add_widget(status_label)
        box.add_widget(generate_btn)

        popup = Popup(title="Upgrade (self-add a feature)", content=box, size_hint=(0.9, 0.7))

        def do_generate(*a):
            instruction = desc_input.text.strip()
            if not instruction:
                return
            api_key = self.config_data.get("api_key", "")
            if not api_key:
                status_label.text = "Set your API key in Settings first."
                return
            status_label.text = "Generating... this can take up to a minute."
            generate_btn.disabled = True

            def work():
                try:
                    filename, code = self_upgrade.generate_plugin(instruction, api_key)
                    self._show_review_popup(filename, code)
                    popup.dismiss()
                except Exception as e:
                    self._set_label(status_label, f"Failed: {e}")
                    self._enable_button(generate_btn)

            threading.Thread(target=work).start()

        generate_btn.bind(on_press=do_generate)
        popup.open()

    @mainthread
    def _set_label(self, label, text):
        label.text = text

    @mainthread
    def _enable_button(self, btn):
        btn.disabled = False

    @mainthread
    def _show_review_popup(self, filename, code):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        box.add_widget(Label(
            text=f"Generated plugin: {filename}\n"
                 f"Review before installing — this code will run with full "
                 f"app permissions (internet, mic, your API key).",
            size_hint_y=None, height=70,
        ))
        scroll = ScrollView()
        code_label = Label(
            text=code, size_hint_y=None, halign="left", valign="top",
            text_size=(self.width * 0.8 if self.width else 400, None),
        )
        code_label.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1]))
        scroll.add_widget(code_label)
        box.add_widget(scroll)

        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        accept_btn = Button(text="Accept & Install")
        reject_btn = Button(text="Reject")
        btn_row.add_widget(accept_btn)
        btn_row.add_widget(reject_btn)
        box.add_widget(btn_row)

        popup = Popup(title="Review generated code", content=box, size_hint=(0.95, 0.9))

        def accept(*a):
            loaded = plugin_loader.install_from_pending(filename)
            popup.dismiss()
            self._add_bubble(f"(Upgrade installed: {filename}. Active plugins: {', '.join(loaded)})")

        def reject(*a):
            plugin_loader.reject_pending(filename)
            popup.dismiss()
            self._add_bubble("(Upgrade rejected — nothing was installed.)")

        accept_btn.bind(on_press=accept)
        reject_btn.bind(on_press=reject)
        popup.open()

    def open_settings(self, *args):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        key_input = TextInput(
            text=self.config_data.get("api_key", ""),
            hint_text="Paste your Anthropic API key here",
            multiline=False,
            password=True,
        )
        speak_row = BoxLayout(size_hint_y=None, height=40)
        speak_label = Label(text="Speak replies aloud")
        speak_toggle = Button(
            text="ON" if self.config_data.get("speak_replies", True) else "OFF",
            size_hint_x=None,
            width=80,
        )

        def toggle_speak(*a):
            new_val = not self.config_data.get("speak_replies", True)
            self.config_data["speak_replies"] = new_val
            speak_toggle.text = "ON" if new_val else "OFF"

        speak_toggle.bind(on_press=toggle_speak)
        speak_row.add_widget(speak_label)
        speak_row.add_widget(speak_toggle)

        rollback_btn = Button(text="Rollback last upgrade", size_hint_y=None, height=45)

        def do_rollback(*a):
            ok = plugin_loader.rollback_last()
            rollback_btn.text = "Rolled back!" if ok else "Nothing to roll back"

        rollback_btn.bind(on_press=do_rollback)

        save_btn = Button(text="Save", size_hint_y=None, height=50)
        box.add_widget(Label(text="API Key (stored only on this device):", size_hint_y=None, height=30))
        box.add_widget(key_input)
        box.add_widget(speak_row)
        box.add_widget(rollback_btn)
        box.add_widget(save_btn)

        popup = Popup(title="Settings", content=box, size_hint=(0.9, 0.5))

        def save(*a):
            self.config_data["api_key"] = key_input.text.strip()
            save_json(CONFIG_PATH, self.config_data)
            popup.dismiss()

        save_btn.bind(on_press=save)
        popup.open()

    def on_send(self, *args):
        message = self.text_input.text.strip()
        if not message:
            return
        self.text_input.text = ""
        self._add_bubble(f"You: {message}")

        self.memory["history"].append({"role": "user", "content": message})
        save_json(MEMORY_PATH, self.memory)

        threading.Thread(target=self._handle_message, args=(message,)).start()

    def _handle_message(self, message):
        plugin_reply = plugin_loader.handle_command(message)
        if plugin_reply is not None:
            self._reply(plugin_reply)
        else:
            self._call_api(message)

    def _call_api(self, message):
        api_key = self.config_data.get("api_key", "")
        if not api_key:
            self._reply("Please set your API key in Settings first.")
            return

        payload = {
            "model": MODEL,
            "max_tokens": 1000,
            "messages": [
                {"role": t["role"], "content": t["content"]}
                for t in self.memory["history"][-10:]
            ],
        }

        req = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = "".join(
                block.get("text", "") for block in data.get("content", [])
                if block.get("type") == "text"
            )
            if not text:
                text = "(no response)"
        except Exception as e:
            text = f"Error calling API: {e}"

        self._reply(text)

    @mainthread
    def _reply(self, text):
        self._add_bubble(f"Assistant: {text}")
        self.memory["history"].append({"role": "assistant", "content": text})
        save_json(MEMORY_PATH, self.memory)
        if self.config_data.get("speak_replies", True):
            speak(text)


class AssistantApp(App):
    def build(self):
        return AssistantRoot()


if __name__ == "__main__":
    AssistantApp().run()
