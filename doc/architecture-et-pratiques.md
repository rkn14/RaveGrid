# Architecture et bonnes pratiques de structuration du code

Ce document décrit des **principes** et des **habitudes de structuration** adaptés à une application qui combine **capture vidéo (OpenCV)**, **détection de motifs**, **affichage** et **audio**. L’objectif est de garder un code **lisible**, **testable** et **évolutif** quand la complexité augmente — sans prescrire les détails fonctionnels du produit.

---

## 1. Séparer les responsabilités (couches logiques)

Évite le fichier unique qui fait tout (boucle caméra, traitement, affichage, sons, configuration). Découpe plutôt en **rôles** clairs :

| Rôle | Responsabilité typique |
|------|-------------------------|
| **Acquisition** | Ouvrir la caméra, lire des images, gérer la résolution / FPS, relâcher les ressources. |
| **Vision / traitement** | Chaînes OpenCV : prétraitement, détection, extraction de résultats structurés (pas d’UI ici). |
| **Domaine** | Types et règles métier : « un motif détecté », états, événements métier — indépendants d’OpenCV quand c’est possible. |
| **Présentation / UI** | Affichage de l’image, surcouches graphiques, rythme d’actualisation de l’écran. |
| **Audio** | Jouer un son, mixer, volumes — derrière une **interface** (voir plus bas). |
| **Orchestration** | Boucle principale ou moteur qui enchaîne acquisition → traitement → mise à jour de l’état → UI / audio. |

**Intérêt** : tu peux changer la caméra (USB, Pi, fichier vidéo), le moteur de détection ou la bibliothèque audio sans réécrire toute l’application.

---

## 2. Inverser les dépendances (interfaces / ports)

Les modules « haut niveau » (orchestration, règles) ne doivent pas dépendre directement d’implémentations concrètes (un seul appel global à OpenCV partout, ou `pygame` éparpillé).

- Définis des **interfaces** (classes abstraites ou `Protocol` en Python) : par ex. `FrameSource`, `Detector`, `AudioOutput`, `Display`.
- Les **implémentations** concrètes (`OpenCvCamera`, `OpenCvDetector`, `SdAudioOutput`, …) vivent à part et sont **injectées** au démarrage (constructeur, fonction `main`, ou petit conteneur simple).

**Pattern** : *Ports and adapters* (hexagonal) — le cœur de l’app parle à des ports ; les adapters branchent OpenCV, le matériel, etc.

**Intérêt** : tests unitaires avec des **fakes** (fausses images, faux audio), et remplacement d’une techno sans toucher au cœur.

---

## 3. Pipeline de vision vs « gros script »

Pour la partie OpenCV :

- Garde les **étapes** identifiables (filtrage, seuillage, détection de contours, etc.) dans des **fonctions ou petites classes** avec entrées/sorties claires (image in → résultat out).
- Préfère le **pipeline explicite** (étape A puis B puis C) à une seule fonction de 400 lignes.
- Si plusieurs stratégies de détection coexistent ou pourront coexister, le **Strategy** (interchangeable derrière une même interface `Detector`) évite les `if/elif` géants.

**Intérêt** : mesurer ou remplacer une étape, réutiliser le même pipeline hors caméra (images de test).

---

## 4. Boucle applicative et flux de données

Une app caméra + UI tourne souvent sur une **boucle** (lecture frame → traitement → affichage / événements).

- Centralise la boucle dans un seul endroit (**application loop** ou **game loop** conceptuel).
- Passe les **résultats du traitement** sous forme de **structures de données** (dataclasses, TypedDict, etc.) vers l’UI et l’audio, plutôt que de laisser le module OpenCV appeler directement l’affichage ou le son.

**Observer / événements** : quand un motif est détecté, émettre un événement ou appeler un petit bus léger peut découpler « détection » de « réaction » (son, compteur, log). Ne surcharge pas avant d’en avoir besoin : une simple fonction callback ou une liste d’observateurs suffit souvent.

---

## 5. État de l’application

Distingue :

- **État court** : dernière frame, résultats du dernier tick.
- **État durable** : préférences utilisateur, seuils, profils de détection.

Évite les **variables globales** modifiées partout. Regroupe l’état dans un **objet ou contexte** passé explicitement (ou un module `state` minimal et documenté si tu restes petit).

**Intérêt** : débogage plus simple, évolution vers sauvegarde / chargement de config.

---

## 6. Configuration

- Constantes magiques (seuils, tailles, chemins) → **fichier de config** (YAML, TOML, `.env` pour secrets) ou section dédiée dans `pyproject` / module `config` chargé une fois.
- Valide les valeurs au démarrage plutôt qu’au milieu d’une boucle caméra.

---

## 7. Gestion des erreurs et du matériel

Caméra débranchée, frame vide, OpenCV en échec : prévois des **chemins d’erreur** clairs (log, message utilisateur, réessai contrôlé) sans faire planter toute la boucle silencieusement.

**Ressources** : utilise des context managers (`with`, ou try/finally) pour **libérer** la caméra et les fichiers proprement à l’arrêt.

---

## 8. Tests et qualité

- **Vision** : images de référence (fixtures) pour vérifier qu’une étape de pipeline retourne le bon type / les bonnes métriques.
- **Orchestration** : avec des doubles de `FrameSource` et `Detector`, tester la logique sans matériel.
- Outils Python utiles à terme : **pytest**, typage progressif (**mypy** ou **Pyright**), formatage (**ruff** / black) — à introduire quand le dépôt grossit.

---

## 9. Organisation des dossiers (exemple indicatif)

Aucune obligation de suivre cette arborescence à la lettre ; elle illustre une **séparation** cohérente avec ce document :

```text
src/ravegrid/
  app/           # boucle principale, assemblage des composants
  capture/       # sources d’images (caméra, fichier…)
  vision/        # pipelines OpenCV, détecteurs
  domain/        # modèles et événements métier
  ui/            # affichage (fenêtre, rendu)
  audio/         # interfaces + implémentations
  config/        # chargement des paramètres
```

Le point d’entrée CLI (`cli.py` ou équivalent) reste **mince** : parse les arguments, charge la config, lance l’app.

---

## 10. Ce qu’il vaut mieux éviter

- **God object** : une classe « Application » qui contient 50 méthodes et tout l’OpenCV.
- **Mélanger** dessin OpenCV et règles métier dans le même module sans frontière.
- **Copier-coller** des blocs de traitement d’image au lieu de factoriser des fonctions réutilisables.
- **Optimiser prématurément** la boucle avant d’avoir une structure lisible ; la structure aide ensuite à profiler une **zone** précise.

---

## 11. Résumé

| Principe | Effet |
|----------|--------|
| Couches (acquisition, vision, domaine, UI, audio) | Changements localisés, code plus clair. |
| Interfaces + injection | Tests, remplacement matériel / libs. |
| Pipeline de vision modulaire | Évolution et debug des étapes. |
| Boucle unique, données structurées | Flux maîtrisé entre détection et réactions. |
| Config et état explicites | Moins de surprises en production. |

Adapte la **granularité** à la taille réelle du projet : au début, quelques modules bien nommés valent mieux qu’une usine à patterns. L’important est de **garder des frontières** nettes pour pouvoir complexifier sans tout casser.
