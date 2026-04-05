# Environnement Python et installation (Linux / Raspberry Pi)

Documentation simple pour comprendre le dossier **`.venv`** et installer **RaveGrid** sur une machine Linux, dont un **Raspberry Pi**.

---

## À quoi sert `.venv` ?

**`.venv`** est un **environnement virtuel Python** : un dossier local qui contient une copie « isolée » de Python et des paquets installés **uniquement pour ce projet**.

- Les paquets que tu installes avec `pip` dans ce venv **ne mélangent pas** les bibliothèques des autres projets ni celles installées au niveau du système.
- Le dépôt liste les dépendances dans **`pyproject.toml`** ; le venv, lui, contient les **fichiers réellement installés** (OpenCV, NumPy, etc.).

**Bon réflexe** : activer le venv avant de travailler, puis utiliser `pip` et `python` comme d’habitude — ils pointeront vers cet environnement.

**À ne pas faire** : ne **copie pas** un dossier `.venv` créé sur Windows vers un Raspberry Pi (ou l’inverse). Les paquets binaires (OpenCV, etc.) sont **spécifiques à l’OS et au processeur**. Sur chaque machine, tu recrées un venv et tu réinstalles avec `pip`.

Le dossier **`.venv`** est ignoré par Git (voir `.gitignore`) : chaque développeur ou chaque appareil a **son propre** venv.

---

## Prérequis sur Linux / Raspberry Pi

- **Python 3.10 ou plus** (`python3 --version`).
- Les outils pour créer un venv. Sur Debian / Raspberry Pi OS :

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
```

*(Si `python3` est trop ancien, installe une version récente ou utilise `pyenv` — le projet demande Python ≥ 3.10.)*

---

## Mode opératoire : installation du projet

1. **Récupérer le code** (clone ou copie du dépôt), puis aller à la racine du projet (là où se trouve `pyproject.toml`).

2. **Créer l’environnement virtuel** :

```bash
python3 -m venv .venv
```

3. **Activer** le venv :

```bash
source .venv/bin/activate
```

Tu devrais voir `(.venv)` au début de la ligne de commande.

4. **Mettre à jour pip** (recommandé) :

```bash
python -m pip install --upgrade pip
```

5. **Installer le projet en mode éditable** (installe aussi les dépendances définies dans `pyproject.toml`, dont OpenCV) :

```bash
pip install -e .
```

6. **Vérifier** :

```bash
ravegrid --version
```

Tu dois voir la version du paquet **ravegrid** et la version **OpenCV**.

Pour quitter le venv plus tard : `deactivate`.

---

## Raspberry Pi sans écran (OpenCV « headless »)

Sur un Pi utilisé **sans interface graphique**, il est souvent préférable d’utiliser **opencv-python-headless** (pas de dépendances GUI inutiles).

Après une installation normale comme ci-dessus :

```bash
source .venv/bin/activate
pip uninstall -y opencv-python
pip install "opencv-python-headless>=4.8,<5"
```

Puis revérifie avec `ravegrid --version`.

---

## Rappel rapide des commandes

| Action              | Commande (Linux, venv activé)   |
|---------------------|----------------------------------|
| Activer le venv     | `source .venv/bin/activate`      |
| Installer / mettre à jour le projet | `pip install -e .`   |
| Lancer la CLI       | `ravegrid --version` ou `python -m ravegrid --version` |
| Désactiver le venv  | `deactivate`                     |

---

## Windows (développement)

Sous **PowerShell**, depuis la racine du projet, l’activation du venv passe par `Activate.ps1`. Si Windows refuse avec **« l’exécution de scripts est désactivée »**, lance d’abord **`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`** : cela n’autorise les scripts **que pour la fenêtre PowerShell ouverte** (rien de permanent sur la machine).

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
ravegrid --version
```

*(Tu peux omettre la ligne `Set-ExecutionPolicy` si l’activation fonctionne déjà.)*

**Sans PowerShell** : dans **cmd**, `.\.venv\Scripts\activate.bat` évite ce blocage. Tu peux aussi appeler directement `.\.venv\Scripts\python.exe -m ravegrid --version` sans activer le venv.
