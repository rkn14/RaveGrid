Application en Python + OpenCV permettant d’analyser en temps réel un plateau physique filmé par une caméra placée au-dessus.

Le système doit :

détecter automatiquement la grille 32 colonnes × 8 lignes à partir de 4 symboles repères placés dans les coins du plateau
corriger la perspective pour reconstruire une vue propre et stable du plateau
représenter la grille à l’écran, avec un affichage numérique fidèle de l’état détecté
analyser chaque case pour identifier la présence d’un élément et détecter sa couleur
mettre à jour l’affichage en temps réel tout en restant robuste aux perturbations visuelles (mains, mouvements, variations de lumière)

L’objectif est de transformer un plateau physique en interface tangible pilotée par vision par ordinateur, avec lecture automatique de son état et restitution visuelle immédiate.