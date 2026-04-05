# Vision — Détection des marqueurs ArUco et homographie

## 1. Marqueurs

| ID ArUco | Coin du plateau | Corner utilisé¹ | Index dans `corners` |
|----------|-----------------|-----------------|----------------------|
| 0        | Haut-gauche     | Bas-droit        | 2                    |
| 1        | Haut-droit      | Bas-gauche       | 3                    |
| 2        | Bas-droit       | Haut-gauche      | 0                    |
| 3        | Bas-gauche      | Haut-droit       | 1                    |

¹ Le corner *intérieur* de chaque marqueur (celui qui touche la grille) définit le coin correspondant de la grille.

**Dictionnaire** : `cv2.aruco.DICT_4X4_50`  
**Taille physique recommandée** : 6 × 6 cm (configurable, sert de référence visuelle).

Les 4 marqueurs à imprimer sont générés par le script `tools/generate_markers.py` (à créer).

---

## 2. Grille

| Paramètre    | Valeur par défaut | Clé config TOML        |
|--------------|-------------------|------------------------|
| Lignes       | 8                 | `grid.rows`            |
| Colonnes     | 32                | `grid.cols`            |

La grille occupe exactement le rectangle défini par les 4 corners intérieurs des marqueurs après correction de perspective.

---

## 3. Pipeline (module `vision/`)

```
frame BGR
  │
  ▼
GrayScale  (cv2.cvtColor)
  │
  ▼
DetectMarkers  (cv2.aruco.ArucoDetector.detectMarkers)
  → ids[], corners[]
  │
  ├─ < 4 marqueurs détectés → retourner None (frame ignorée)
  │
  ▼
Extraction des 4 points source
  src[0] = corners[id==0][2]   # haut-gauche
  src[1] = corners[id==1][3]   # haut-droit
  src[2] = corners[id==2][0]   # bas-droit
  src[3] = corners[id==3][1]   # bas-gauche
  │
  ▼
Homographie  (cv2.getPerspectiveTransform)
  dst = rectangle fixe OUTPUT_W × OUTPUT_H pixels
  │
  ▼
Redressement  (cv2.warpPerspective)
  → image plateau rectifiée (OUTPUT_W × OUTPUT_H)
  │
  ▼
GridState  (découpage en rows × cols cellules)
  → liste de tuples (row, col, image_cellule)
```

**Dimensions de sortie** : `OUTPUT_W = cols * CELL_PX`, `OUTPUT_H = rows * CELL_PX`  
`CELL_PX = 64` (configurable — `grid.cell_px`).

---

## 4. Structures de données (module `domain/`)

```python
@dataclass
class MarkerDetection:
    id: int
    corners: np.ndarray        # shape (4, 2), float32

@dataclass
class BoardCorners:
    top_left:     np.ndarray   # shape (2,), float32
    top_right:    np.ndarray
    bottom_right: np.ndarray
    bottom_left:  np.ndarray

@dataclass
class GridState:
    rows: int
    cols: int
    cells: np.ndarray          # shape (rows, cols, CELL_PX, CELL_PX, 3), uint8
    timestamp: float
```

---

## 5. Configuration (`config.toml`)

```toml
[grid]
rows    = 8
cols    = 32
cell_px = 64          # résolution en pixels d'une cellule dans l'image rectifiée

[aruco]
dictionary = "DICT_4X4_50"
marker_border_bits = 1    # épaisseur de la bordure ArUco (défaut OpenCV)
```

---

## 6. Modules à créer

| Fichier                          | Rôle                                                    |
|----------------------------------|---------------------------------------------------------|
| `vision/board_detector.py`       | `BoardDetector` : detectMarkers → `BoardCorners`        |
| `vision/rectifier.py`            | `Rectifier` : `BoardCorners` + frame → image rectifiée |
| `vision/grid_splitter.py`        | `GridSplitter` : image rectifiée → `GridState`          |
| `domain/board.py`                | Dataclasses `MarkerDetection`, `BoardCorners`, `GridState` |
| `config/schema.py`               | Ajouter `GridConfig`, `ArucoConfig`                     |
| `tools/generate_markers.py`      | Script one-shot : génère et sauvegarde les 4 PNG        |

---

## 7. Comportement en cas d'occlusion partielle

- **< 4 marqueurs** : le détecteur retourne `None`. La boucle principale conserve le dernier `GridState` valide.
- Un paramètre `vision.max_missing_frames` (défaut : `10`) définit après combien de frames consécutives sans détection l'état est considéré invalide et l'affichage signale la perte.
