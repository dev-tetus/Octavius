# Octavius 🏛️
🌍 Idiomas disponibles / Available languages  / Langues disponibles:

- ![UK](https://flagcdn.com/w20/gb.png) [Read here in english](README.en.md)
- ![FR](https://flagcdn.com/w20/fr.png) [Lire ici en français](README.fr.md)

**Octavius** es un **asistente vocal** pensado para el **acompañamiento de personas mayores**.  
Inspirado en la pasión de mis abuelas por la historia de Roma, el nombre honra a ***Gaius Octavius → Augustus***, el primer emperador romano.  
La idea es sencilla: un **dispositivo accesible y cercano**, que permita hablar directamente con él sin necesidad de manipularlo, ofreciendo compañía, interacción natural y ayuda en la vida cotidiana.

---

## ✨ Descripción

Octavius busca ser más que un simple asistente de voz.  
El proyecto combina tecnología de **reconocimiento de voz (ASR)**, **síntesis de voz (TTS)** y un **motor de diálogo** para ofrecer conversaciones fluidas y naturales.  

El dispositivo estará orientado principalmente a **personas mayores**, con los siguientes pilares:

- **Accesibilidad**: interacción sin pantallas, solo con voz (aunque más adelante podrá incluir una pantalla para configuración y nuevas funciones).  
- **Sencillez**: configuración mínima y uso inmediato.  
- **Acompañamiento**: generar conversación, compañía y sensación de cercanía.  
- **Evolución**: añadir funciones adaptadas a necesidades reales (recordatorios, lecturas, etc.).

---

## 🎯 Objetivos

- Crear un **compañero digital accesible** para personas mayores.  
- Facilitar la **interacción natural mediante voz** (preguntas, charlas, consultas sencillas).  
- Acompañar en la vida cotidiana, con la posibilidad de añadir funciones como:  
  - Recordatorios de medicación  
  - Reproducción de música o cuentos  
  - Lectura de noticias  
  - Conversaciones sobre historia, curiosidades, temas de interés  

---

## 🚀 Propuesta inicial de despliegue

⚠️ *Pendiente de definición para Raspberry Pi 4*  

Por ahora, Octavius se ejecuta en **PC de escritorio** para desarrollo y pruebas.

---

## 🛠️ Stack tecnológico

El proyecto combina distintas piezas tecnológicas:

- **Python** (backend principal)  
- **PyAudio** (captura y reproducción de audio)  
- **NumPy / SciPy** (procesamiento de señales, resampling)  
- **SoundFile** (lectura/escritura de WAV)  
- **WebRTC VAD** (detección de actividad de voz)  
- **ASR** (Automatic Speech Recognition): [Whisper](https://github.com/openai/whisper) o [Vosk](https://alphacephei.com/vosk/)  
- **TTS** (Text to Speech): [pyttsx3](https://pyttsx3.readthedocs.io/), [gTTS](https://pypi.org/project/gTTS/), u otra opción adaptable  (**TBD**)
- **Motor de diálogo**: modelo GPT para conversaciones naturales  
- **Logging centralizado** con la utilidad propia del proyecto 

---

## 🖥️ Instrucciones para levantar el proyecto en PC

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/<tu-usuario>/<tu-repo>.git
   cd octavius
   ```
2. **Crear entorno virtual**
    ```bash
    python -m venv octavius-env
    source octavius-env/bin/activate   # Linux/Mac
    .\octavius-env\Scripts\activate    # Windows
    ```
3. **Instalar dependencias**
    ```bash
    pip install -r requirements.txt
    ```
4. **Ejecutar el asistente**
    ```bash
    python -m octavius.main
    ```
---

## 📌 Próximos pasos

- [ ] Definir despliegue en Raspberry Pi 4  
- [ ] Integrar VAD para grabación automática hasta silencio  
- [ ] Conectar ASR (Whisper/Vosk)  
- [ ] Conectar TTS (voz de salida)  
- [ ] Añadir motor de diálogo GPT  
- [ ] Diseñar interfaz de configuración básica  

---

## ❤️ Créditos

Proyecto personal en homenaje a mis abuelas, amantes de la historia de Roma.  
Octavius busca unir **tecnología** y **humanidad** para mejorar el día a día de nuestros mayores.