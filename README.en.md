# Octavius 🏛️
🌍 Idiomas disponibles / Available languages  / Langues disponibles

- ![ES](https://flagcdn.com/w20/es.png) [Leer aquí en español](README.md)
- ![FR](https://flagcdn.com/w20/fr.png) [Lire ici en français](README.fr.md)

**Octavius** is a **voice assistant** designed for the **companionship of elderly people**.  
Inspired by my grandmothers’ passion for Roman history, the name honors ***Gaius Octavius → Augustus***, the first Roman emperor.  
The idea is simple: an **accessible and familiar device** that allows people to talk directly to it without manipulation, offering company, natural interaction, and daily support.

---

## ✨ Description

Octavius aims to be more than just a voice assistant.  
The project combines **Automatic Speech Recognition (ASR)**, **Text-to-Speech (TTS)**, and a **dialogue engine** to provide smooth and natural conversations.  

The device will be mainly oriented towards **elderly people**, built on the following pillars:

- **Accessibility**: interaction without screens, only with voice (later on, it could include a screen for configuration and new features).  
- **Simplicity**: minimal configuration and immediate use.  
- **Companionship**: generate conversation, presence, and a sense of closeness.  
- **Evolution**: add functions adapted to real needs (reminders, readings, etc.).

---

## 🎯 Goals

- Create an **accessible digital companion** for elderly people.  
- Enable **natural voice interaction** (questions, chats, simple queries).  
- Provide support in daily life, with possible features such as:  
  - Medication reminders  
  - Playing music or stories  
  - Reading news  
  - Conversations about history, curiosities, and topics of interest  

---

## 🚀 Initial deployment proposal

⚠️ *Pending definition for Raspberry Pi 4*  

For now, Octavius runs on a **desktop PC** for development and testing.

---

## 🛠️ Technology stack

The project combines different technologies:

- **Python** (main backend)  
- **PyAudio** (audio capture and playback)  
- **NumPy / SciPy** (signal processing, resampling)  
- **SoundFile** (WAV read/write)  
- **WebRTC VAD** (voice activity detection)  
- **ASR** (Automatic Speech Recognition): [Whisper](https://github.com/openai/whisper) or [Vosk](https://alphacephei.com/vosk/)  
- **TTS** (Text-to-Speech): [pyttsx3](https://pyttsx3.readthedocs.io/), [gTTS](https://pypi.org/project/gTTS/), or another adaptable option (**TBD**)  
- **Dialogue engine**: GPT model for natural conversations  
- **Centralized logging** with the project’s utility  

---

## 🖥️ Instructions to run the project on PC

1. **Clone the repository**
   ```bash
   git clone https://github.com/<tu-usuario>/<tu-repo>.git
   cd octavius
   ```
2. **Create virtual environment**
    ```bash
    python -m venv octavius-env
    source octavius-env/bin/activate   # Linux/Mac
    .\octavius-env\Scripts\activate    # Windows
    ```
3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4. **Run the assistant**
    ```bash
    python -m octavius.main
    ```
---

## 📌 Next steps

- [ ] Define deployment on Raspberry Pi 4
- [ ] Integrate VAD for automatic recording until silence
- [ ] Connect ASR (Whisper/Vosk)  
- [ ] Connect TTS (voice output)
- [ ] Add GPT dialogue engine
- [ ] Design basic configuration interface

---

## ❤️ Credits

Personal project in tribute to my grandmothers, lovers of Roman history.
Octavius aims to unite technology and humanity to improve the daily lives of elderly people.