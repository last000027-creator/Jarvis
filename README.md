# My Assistant (starter core)

A minimal, working personal assistant app for Android, built with Python + Kivy.
This is the **foundation** — a real chat app that talks to the Claude API and
remembers conversation history on your device. Voice, smart home control,
self-upgrade, and all the other features you listed can be added later as
plugins on top of this.

## What's included
- `main.py` — the app (chat UI + API call + local memory + settings screen for your API key)
- `plugins/voice.py` — voice output (assistant speaks replies aloud) and
  voice input (tap the 🎤 button to talk instead of typing, using Android's
  built-in speech recognizer)
- `plugins/plugin_loader.py` + `plugins/self_upgrade.py` — **NEW: the
  self-upgrade feature.** Tap **Upgrade**, describe a feature in plain
  words (e.g. "tell me a joke when I say 'joke'"), and Claude writes a
  small plugin file implementing it. You're shown the generated code and
  must tap **Accept** before it's installed and active, or **Reject** to
  discard it. Installed plugins get first chance to answer your messages;
  anything they don't handle still goes to the main Claude API as before.
  A **"Rollback last upgrade"** button in Settings undoes the most recent
  install if something goes wrong.
- `buildozer.spec` — tells Buildozer how to package the app as an Android APK
- `.github/workflows/build.yml` — GitHub Actions workflow that automatically builds
  the APK in the cloud every time you push code (no Android Studio needed)

### ⚠️ About self-upgrade specifically
This is the highest-risk feature in the app, by design of what it does:
- Generated code runs with the same permissions as the rest of the app
  (internet, microphone, your stored API key). Only tap Accept on code you've
  at least skimmed and are comfortable with — treat it like code you'd paste
  in from a stranger on the internet, because in a sense, that's what it is.
- It can't rebuild the compiled APK itself — it adds a plugin file to the
  app's own writable data folder and loads it into the running app. This
  works without a full rebuild, but a plugin can still have bugs; that's what
  the review step and rollback button are for.
- This was written using well-established patterns but, like the voice
  feature, **could not be run or tested on a real device from this
  environment.** Try a small, low-risk feature first (like a joke responder)
  before trusting it with anything sensitive.

### ⚠️ About the voice feature specifically
This was written and packaged here but **could not be run or tested on a real
device** in this environment (no Android hardware/emulator available). It uses
well-established Android APIs (`SpeechRecognizer`, `TextToSpeech`) via pyjnius,
but voice/audio code is exactly the kind of thing that sometimes needs a small
fix once it hits a real phone. If it doesn't work first try:
- Check you tapped "Allow" on the microphone permission popup (should appear
  the first time you tap 🎤)
- Look at the on-screen error bubble it prints if something fails — it's
  designed to show you the actual error rather than silently do nothing
- Text chat (typing) will keep working regardless, since voice is a separate
  add-on and not required for the app to function

## How to get your APK

1. **Create a new GitHub repository** (e.g. `my-assistant`).
2. **Upload all the files in this zip**, keeping the folder structure exactly
   as-is (the `.github/workflows/build.yml` file must stay inside `.github/workflows/`).
3. Push/commit to the `main` branch.
4. Go to the **Actions** tab on your GitHub repo. You'll see a workflow run
   start automatically ("Build APK").
5. Wait for it to finish (first build can take 15-30 minutes — it's compiling
   Python and Android tools from scratch).
6. Click the finished run → scroll to **Artifacts** → download `myassistant-apk`.
   Unzip it to get your `.apk` file.
7. Transfer the `.apk` to your Android phone and install it (you'll need to
   allow "install from unknown sources" in Android settings, since it's not
   from the Play Store).

## First run on your phone
1. Open the app.
2. Tap **Settings**, paste in your Anthropic API key (get one at
   console.anthropic.com), tap Save.
3. Type a message and hit Send. The assistant will reply using Claude.

Your API key and chat history are stored only in the app's local files on
your device — nothing is sent anywhere except directly to the Anthropic API
when you send a message.

## Where to go next
This is intentionally a small, working core so it's easy to understand and
safe to build on. Good next steps, one at a time:
- Add voice input/output (speech-to-text and text-to-speech libraries)
- Add a "plugins" folder where each feature lives in its own file
- Add reminders, calendar, or web search as your first plugin
- Later: the "upgrade itself by voice command" feature — have the assistant
  generate a new plugin file when you ask it to add a feature, then reload it

Build one feature, test it, then add the next. That's how every real
assistant app (including the big ones) actually got built.
