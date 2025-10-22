# MapAlya_V4

## 🎯 Extracteur EDI Adaptatif Multi-Format

Extraction automatique de spécifications EDI depuis des fichiers PDF avec détection automatique du format.  
Supporte **Faurecia EDI Guideline** et **VDA 4932 (Automotive standard)**.

### ✨ Fonctionnalités

- � **Détection automatique** : Identifie le format du PDF (Faurecia, VDA 4932)
- 📄 **Extraction complète** : Segments, groupes, champs, formats, valeurs et usages
- 🏗️ **Structure hiérarchique** : Organisation conforme aux standards EDI
- 📊 **Haute précision** : 99-100% formats, 57-76% valeurs, 41-74% usages
- 🚀 **Traitement en masse** : Extrait tous les PDF d'un dossier automatiquement
- � **Export JSON standardisé** : Format uniforme pour tous les types de PDF

### 🚀 Démarrage rapide

1. **Installation des dépendances**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Extraction d'un fichier spécifique**
   ```powershell
   python extract_edi_adaptive.py "nom_du_fichier.pdf"
   ```

3. **Traitement en masse (tous les PDF)**
   ```powershell
   python extract_all_pdfs.py
   ```

### 📂 Structure du projet

```
MapAlya_V4/
├── extract_edi_adaptive.py           # 🔧 Extracteur adaptatif principal
├── extract_all_pdfs.py               # 🚀 Traitement en masse
├── requirements.txt                  # 📦 Dépendances Python
├── schema/                           # 📁 Dossier source des PDF
│   ├── exemple_export.json           # 📝 Format de sortie attendu
│   ├── Faurecia EDI Guideline INVOIC D96A V2R6.pdf
│   └── INVOICE4932englisch.pdf       # 📄 VDA 4932
├── export/                           # � Exports JSON générés
│   ├── Faurecia_EDI_Guideline_INVOIC_D96A_V2R6.json
│   └── INVOICE4932englisch.json
└── copilot/                          # 🛠️ Scripts utilitaires
    ├── compare_extractions.py        # � Comparaison des résultats
    ├── verify_vda_extraction.py      # ✅ Vérification VDA
    └── analyze_*.py                  # � Outils d'analyse
```

### 📖 Scripts disponibles

| Script | Description |
|--------|-------------|
| `extract_edi_adaptive.py` | 🔧 Extracteur adaptatif multi-format (principal) |
| `extract_all_pdfs.py` | 🚀 Traitement en masse de tous les PDF |
| `copilot/compare_extractions.py` | 📊 Compare les extractions Faurecia vs VDA |
| `copilot/verify_vda_extraction.py` | ✅ Vérifie l'extraction VDA 4932 |
| `copilot/analyze_*.py` | 🔍 Outils d'analyse de structure PDF |

### 📊 Format de sortie

Le JSON généré suit cette structure standardisée :

```json
[
    {
        "segment": "UNH",
        "description": "Message header",
        "elements": [
            {
                "champ": "0062",
                "description": "Message reference number",
                "format": "M an..14",
                "valeur": "+0001",
                "usage": "Sequential number (R, an..14)"
            },
            {
                "groupe": "S009",
                "description": "Message identifier",
                "champs": [
                    {
                        "champ": "0065",
                        "description": "Message type identifier",
                        "format": "M an..6",
                        "valeur": "+INVOIC",
                        "usage": "INVOIC = Invoice Message"
                    }
                ]
            }
        ]
    }
]
```

### 🎯 Formats supportés

#### ✅ Faurecia EDI Guideline
- Structure : Tables avec colonnes Code/Description/Format/Valeur/Usage
- Pattern : `Segment: Pos.: N Level: N`
- Extraction : 24 segments, 356 éléments, **99.4% formats, 73.6% usages**

#### ✅ VDA 4932 (Automotive Standard)
- Structure : Sections avec `Segment: XXX Cons. No.: N Level: N`
- Pattern : Tables avec `CODE Description | Format | Exemple | Usage`
- Extraction : 33 segments, 696 éléments, **100% formats, 41.4% usages**

### 📚 Documentation

- **Guide complet** : `copilot/EXTRACT_EDI_README.md`
- **Guides d'extraction** : Voir dossier `copilot/`

### 🛠️ Technologies utilisées

- **Python 3.10+**
- **pdfplumber ≥ 0.10.0** : Extraction de tableaux depuis PDF
- **PyPDF2 ≥ 3.0.0** : Lecture de PDF alternatif

### 📈 Résultats de l'extraction

#### Faurecia EDI Guideline INVOIC D96A V2R6
- ✅ **24 segments** EDI
- ✅ **356 éléments** (28 simples + 328 dans groupes)
- ✅ **354 formats** (99.4%)
- ✅ **271 valeurs** (76.1%)
- ✅ **262 usages** (73.6%)

#### INVOICE4932 (VDA 4932)
- ✅ **33 segments** EDI
- ✅ **696 éléments** (64 simples + 632 dans groupes)
- ✅ **696 formats** (100%)
- ✅ **398 valeurs** (57.2%)
- ✅ **288 usages** (41.4%)

### 💡 Exemples d'utilisation

#### Extraire un fichier spécifique
```powershell
python extract_edi_adaptive.py "INVOICE4932englisch.pdf"
```

#### Traiter tous les PDF
```powershell
python extract_all_pdfs.py
# Appuyez sur Entrée pour traiter tous les fichiers
```

#### Comparer les résultats
```powershell
python copilot/compare_extractions.py
```

### 🤝 Contribution

Les fichiers de travail et utilitaires sont dans le dossier `copilot/`.

### 📝 License

Projet interne MapAlya V4

