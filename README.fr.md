# Octavius 🏛️
🌍 Idiomas disponibles / Available languages  / Langues disponibles:

- ![ES](https://flagcdn.com/w20/es.png) [Leer aquí en español](README.md)
- ![EN](https://flagcdn.com/w20/gb.png) [Read here in english](README.en.md)

**Octavius** est un **assistant vocal** conçu pour l’**accompagnement des personnes âgées**.  
Inspiré par la passion de mes grands-mères pour l’histoire romaine, le nom rend hommage à ***Gaius Octavius → Augustus***, le premier empereur romain.  
L’idée est simple : un **appareil accessible et proche**, permettant de parler directement sans manipulation, offrant compagnie, interaction naturelle et aide au quotidien.

---

## ✨ Description

Octavius vise à être plus qu’un simple assistant vocal.  
Le projet combine la **reconnaissance vocale (ASR)**, la **synthèse vocale (TTS)** et un **moteur de dialogue** pour offrir des conversations fluides et naturelles.  

L’appareil sera principalement destiné aux **personnes âgées**, autour de ces piliers :

- **Accessibilité** : interaction sans écran, uniquement par la voix (plus tard, possibilité d’ajouter un écran pour la configuration et de nouvelles fonctions).  
- **Simplicité** : configuration minimale et usage immédiat.  
- **Accompagnement** : générer des conversations, une présence et un sentiment de proximité.  
- **Évolution** : ajouter des fonctions adaptées aux besoins réels (rappels, lectures, etc.).

---

## 🎯 Objectifs

- Créer un **compagnon numérique accessible** pour les personnes âgées.  
- Faciliter l’**interaction naturelle par la voix** (questions, discussions, requêtes simples).  
- Accompagner la vie quotidienne avec des fonctions possibles telles que :  
  - Rappels de prise de médicaments  
  - Lecture de musique ou d’histoires  
  - Lecture des nouvelles  
  - Conversations sur l’histoire, les curiosités, les thèmes d’intérêt  

---

## 🚀 Proposition initiale de déploiement

⚠️ *En attente de définition pour Raspberry Pi 4*  

Pour l’instant, Octavius s’exécute sur un **PC de bureau** pour le développement et les tests.

---

## 🛠️ Pile technologique

Le projet combine plusieurs technologies :

- **Python** (backend principal)  
- **PyAudio** (capture et lecture audio)  
- **NumPy / SciPy** (traitement du signal, rééchantillonnage)  
- **SoundFile** (lecture/écriture de WAV)  
- **WebRTC VAD** (détection d’activité vocale)  
- **ASR** (Automatic Speech Recognition) : [Whisper](https://github.com/openai/whisper) ou [Vosk](https://alphacephei.com/vosk/)  
- **TTS** (Text-to-Speech) : [pyttsx3](https://pyttsx3.readthedocs.io/), [gTTS](https://pypi.org/project/gTTS/), ou autre option adaptable (**TBD**)  
- **Moteur de dialogue** : modèle GPT pour des conversations naturelles  
- **Journalisation centralisée** avec l’utilitaire du projet  

---

## 🖥️ Instructions pour lancer le projet sur PC

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/<tu-usuario>/<tu-repo>.git
   cd octavius
   ```
2. **Créer un environnement virtuel**
    ```bash
    python -m venv octavius-env
    source octavius-env/bin/activate   # Linux/Mac
    .\octavius-env\Scripts\activate    # Windows
    ```
3. **Installer les dépendances**
    ```bash
    pip install -r requirements.txt
    ```
4. **Exécuter l’assistant**
    ```bash
    python -m octavius.main
    ```
---

## 📌 Prochaines étapes

- [ ] Définir le déploiement sur Raspberry Pi 4  
- [ ] Intégrer VAD pour un enregistrement automatique jusqu’au silence  
- [ ] Connecter l’ASR (Whisper/Vosk)
- [ ] Connecter le TTS (voix de sortie)
- [ ] Ajouter le moteur de dialogue GPT  
- [ ] Concevoir une interface de configuration basique

---

## ❤️ Crédits

Projet personnel en hommage à mes grands-mères, passionnées d’histoire romaine.
Octavius vise à unir technologie et humanité pour améliorer la vie quotidienne de nos aînés.