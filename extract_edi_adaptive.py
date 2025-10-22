"""
Extracteur EDI ADAPTATIF - Détecte automatiquement le format du PDF
Supporte :
- Format Faurecia (tables avec colonnes Code/Description/Format/Valeur/Usage)
- Format VDA 4932 (sections "Segment: XXX Cons. No.: XX")
"""

import re
import json
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class AdaptiveEDIExtractor:
    """Extracteur adaptatif pour différents formats de PDF EDI"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.segments_dict = {}
        self.pdf_format = None  # 'faurecia' ou 'vda4932'
    
    def detect_pdf_format(self) -> str:
        """Détecte automatiquement le format du PDF"""
        print("🔍 Détection du format PDF...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            # Analyser les 10 premières pages
            for page in pdf.pages[:10]:
                text = page.extract_text() if page.extract_text() else ""
                
                # Format VDA 4932 : "Segment: NAD Cons. No.: 14 Level: 1"
                if re.search(r'Segment:\s+[A-Z]{3}\s+Cons\.\s*No\.:', text):
                    print("   ✓ Format détecté: VDA 4932 (Automotive standard)\n")
                    return 'vda4932'
                
                # Format Faurecia : "Segment: Pos.: N Level: N" ou ligne séparée
                # Pattern 1: Tout sur une ligne (rare)
                if re.search(r'Segment:.*Pos\.:\s*\d+.*Level:', text):
                    print("   ✓ Format détecté: Faurecia EDI Guideline\n")
                    return 'faurecia'
                
                # Pattern 2: "Segment: Pos.: N" sur des lignes séparées (courant)
                if re.search(r'Segment:\s+Pos\.:\s*\d+\s+Level:', text):
                    print("   ✓ Format détecté: Faurecia EDI Guideline\n")
                    return 'faurecia'
                
                # Pattern 3: Détecter simplement la présence de "Pos.:" et segments UNH/BGM/etc
                if 'Pos.:' in text and re.search(r'\b(UNH|BGM|DTM|NAD|LIN|MOA)\b', text):
                    print("   ✓ Format détecté: Faurecia EDI Guideline\n")
                    return 'faurecia'
        
        print("   ⚠️  Format inconnu, utilisation du format générique par défaut\n")
        return 'faurecia'
    
    def extract_all(self) -> List[Dict[str, Any]]:
        """Pipeline complet d'extraction adaptative"""
        print(f"{'='*70}")
        print("EXTRACTION ADAPTATIVE EDI")
        print(f"{'='*70}\n")
        
        # Détection du format
        self.pdf_format = self.detect_pdf_format()
        
        # Extraction selon le format
        if self.pdf_format == 'vda4932':
            self.extract_vda4932_format()
        else:
            self.extract_faurecia_format()
        
        # Enrichissement
        self.add_standard_descriptions()
        
        # Statistiques
        stats = self.get_statistics()
        
        print(f"{'='*70}")
        print("STATISTIQUES FINALES")
        print(f"{'='*70}")
        print(f"Segments                : {stats['segments']}")
        print(f"Éléments simples        : {stats['simple_elements']}")
        print(f"Groupes composites      : {stats['groups']}")
        print(f"Éléments dans groupes   : {stats['elements_in_groups']}")
        print(f"Total éléments          : {stats['simple_elements'] + stats['elements_in_groups']}")
        print(f"Éléments avec format    : {stats['elements_with_format']}")
        print(f"Éléments avec valeur    : {stats['elements_with_value']}")
        print(f"Éléments avec usage     : {stats['elements_with_usage']} 🎯")
        print(f"{'='*70}\n")
        
        return list(self.segments_dict.values())
    
    def extract_vda4932_format(self):
        """Extrait les segments du format VDA 4932"""
        print("📖 Extraction format VDA 4932...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                # Chercher les segments : "Segment: NAD Cons. No.: 14 Level: 1 Name and address"
                segment_matches = re.finditer(
                    r'Segment:\s+([A-Z]{3})\s+Cons\.\s*No\.:\s*(\d+)\s+Level:\s*(\d+)\s+(.*?)(?=\n|$)',
                    text
                )
                
                for match in segment_matches:
                    segment_code = match.group(1)
                    cons_no = match.group(2)
                    level = match.group(3)
                    description = match.group(4).strip()
                    
                    # Créer ou mettre à jour le segment
                    if segment_code not in self.segments_dict:
                        self.segments_dict[segment_code] = {
                            "segment": segment_code,
                            "description": description,
                            "elements": []
                        }
                
                # Extraire les tableaux de données
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 3:
                        continue
                    
                    self._parse_vda_table(table, page_num)
        
        print(f"   ✓ {len(self.segments_dict)} segments trouvés\n")
    
    def _parse_vda_table(self, table: List[List[str]], page_num: int):
        """Parse un tableau VDA 4932 avec la vraie structure"""
        if not self.segments_dict:
            return
        
        # Dernier segment traité
        last_segment = list(self.segments_dict.values())[-1]
        current_group = None
        
        for row_idx, row in enumerate(table):
            if not row or len(row) < 2:
                continue
            
            row_clean = [str(cell).strip() if cell else '' for cell in row]
            
            # Col 0 contient "CODE Description" (ex: "3035 Party qualifier")
            col0 = row_clean[0] if row_clean else ''
            col1 = row_clean[1] if len(row_clean) > 1 else ''  # Format
            col2 = row_clean[2] if len(row_clean) > 2 else ''  # Exemple/Valeur
            col3 = row_clean[3] if len(row_clean) > 3 else ''  # Usage/Application
            
            # Ignorer les lignes d'en-tête
            if not col0 or col0.startswith('S.Format') or 'Segment can/must' in col0:
                continue
            
            # Extraire le code et la description de col0
            # Patterns: "3035 Party qualifier" ou "C082 Party identification details"
            code_match = re.match(r'^([SC]?\d{3,4})\s+(.+)$', col0)
            if not code_match:
                continue
            
            code = code_match.group(1)
            description = code_match.group(2).strip()
            
            # Nettoyer la description
            description = self.clean_description(description)
            
            # Nettoyer le format (col1)
            format_str = col1.strip()
            
            # Nettoyer la valeur (col2)
            valeur = col2.strip()
            
            # Collecter tous les usages multi-lignes (col3)
            usage_clean = ''
            if col3 and col3.strip() != '--':
                usage_parts = [col3.strip()]
                next_idx = row_idx + 1
                # Look-ahead pour les lignes suivantes d'usage
                while next_idx < len(table):
                    next_row = table[next_idx]
                    if not next_row or len(next_row) < 4:
                        break
                    next_row_clean = [str(cell).strip() if cell else '' for cell in next_row]
                    next_code = next_row_clean[0]
                    next_usage = next_row_clean[3] if len(next_row_clean) > 3 else ''
                    
                    # Si la ligne suivante a un code, on arrête la consolidation
                    if next_code and (re.match(r'^\d{4}$', next_code) or re.match(r'^[SC]\d{3}$', next_code)):
                        break
                    
                    # Si la ligne contient un usage avec pattern 'XXX'= ou code=, on l'ajoute
                    if next_usage and (re.match(r"^['\"]?[A-Z0-9]+['\"]?\s*=", next_usage.strip()) or 
                                       re.match(r'^[A-Z][a-z]+\s+[A-Z]', next_usage.strip())):
                        usage_parts.append(next_usage.strip())
                        next_idx += 1
                    else:
                        break
                
                usage_clean = '\n'.join(usage_parts) if usage_parts else ''
            
            # Groupe composite (C082, S001, etc.)
            if re.match(r'^[SC]\d{3}$', code):
                current_group = {
                    "groupe": code,
                    "description": description,
                    "champs": []
                }
                last_segment["elements"].append(current_group)
            
            # Élément de données (3035, 1131, 3039, etc.)
            elif re.match(r'^\d{4}$', code):
                element = {
                    "champ": code,
                    "description": description,
                    "format": format_str,
                    "valeur": valeur,
                    "usage": usage_clean
                }
                
                if current_group:
                    current_group["champs"].append(element)
                else:
                    last_segment["elements"].append(element)
    
    def extract_faurecia_format(self):
        """Extrait les segments du format Faurecia (code existant)"""
        print("📖 Extraction format Faurecia...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 5:
                        continue
                    
                    self._parse_faurecia_table(table, page_num)
        
        print(f"   ✓ {len(self.segments_dict)} segments trouvés\n")
    
    def _parse_faurecia_table(self, table: List[List[str]], page_num: int):
        """Parse un tableau Faurecia (code existant optimisé)"""
        current_segment = None
        current_group = None
        
        for row_idx, row in enumerate(table):
            if not row:
                continue
            
            row_clean = [str(cell).strip() if cell else '' for cell in row]
            row_text = ' '.join(row_clean)
            
            # Détecter l'en-tête de segment
            segment_match = re.search(r'Segment:\s*([A-Z]{3})', row_text)
            if segment_match:
                current_segment = segment_match.group(1)
                desc_match = re.search(r'Pos\.:\s*\d+.*?([A-Z][\w\s/]+)$', row_text)
                description = desc_match.group(1).strip() if desc_match else ""
                
                if current_segment not in self.segments_dict:
                    self.segments_dict[current_segment] = {
                        "segment": current_segment,
                        "description": self.clean_description(description),
                        "elements": []
                    }
                current_group = None
                continue
            
            if not current_segment:
                continue
            
            # Extraire les colonnes
            code = row_clean[0] if len(row_clean) > 0 else ''
            description = row_clean[1] if len(row_clean) > 1 else ''
            format_str = row_clean[4] if len(row_clean) > 4 else ''
            valeur = row_clean[6] if len(row_clean) > 6 else ''
            usage_desc = row_clean[7] if len(row_clean) > 7 else ''
            
            # Nettoyer
            description = self.clean_description(description)
            format_clean = ' '.join(format_str.split()) if format_str else ''
            valeur_clean = valeur.strip() if valeur else ''
            
            # Collecter tous les usages multi-lignes
            usage_clean = ''
            if usage_desc:
                usage_parts = [usage_desc.strip()]
                next_idx = row_idx + 1
                while next_idx < len(table):
                    next_row = table[next_idx]
                    if not next_row or len(next_row) < 8:
                        break
                    next_row_clean = [str(cell).strip() if cell else '' for cell in next_row]
                    next_code = next_row_clean[0]
                    next_usage = next_row_clean[7] if len(next_row_clean) > 7 else ''
                    if next_code and (re.match(r'^\d{4}$', next_code) or re.match(r'^[SC]\d{3}$', next_code)):
                        break
                    if next_usage and re.match(r'^[A-Z0-9]+\s*=', next_usage.strip()):
                        usage_parts.append(next_usage.strip())
                        next_idx += 1
                    else:
                        break
                usage_clean = '\n'.join(usage_parts) if usage_parts else ''
            
            # Groupe composite
            if re.match(r'^[SC]\d{3}$', code):
                current_group = {
                    "groupe": code,
                    "description": description,
                    "champs": []
                }
                self.segments_dict[current_segment]["elements"].append(current_group)
            
            # Élément de données
            elif re.match(r'^\d{4}$', code):
                element = {
                    "champ": code,
                    "description": description,
                    "format": format_clean,
                    "valeur": valeur_clean,
                    "usage": usage_clean
                }
                if current_group:
                    current_group["champs"].append(element)
                else:
                    self.segments_dict[current_segment]["elements"].append(element)
    
    def clean_description(self, description: str) -> str:
        """Nettoie la description"""
        if not description:
            return ""
        cleaned = re.sub(r'\s+[MC]\s+[MCN](\s+.*)?$', '', description)
        cleaned = re.sub(r'\s+NOT\s+USED$', '', cleaned)
        return cleaned.strip()
    
    def add_standard_descriptions(self):
        """Ajoute les descriptions EDIFACT standard"""
        print("📚 Ajout des descriptions standard...")
        
        standard_descriptions = {
            "UNB": "Interchange header", "UNH": "Message header",
            "BGM": "Beginning of message", "DTM": "Date/time/period",
            "RFF": "Reference", "NAD": "Name and address",
            "CTA": "Contact information", "COM": "Communication contact",
            "TAX": "Duty/tax/fee details", "CUX": "Currencies",
            "PAT": "Payment terms basis", "PCD": "Percentage details",
            "MOA": "Monetary amount", "LIN": "Line item",
            "PIA": "Additional product id", "IMD": "Item description",
            "QTY": "Quantity", "ALI": "Additional information",
            "GIN": "Goods identity number", "GIR": "Related identification numbers",
            "QVR": "Quantity variances", "DOC": "Document/message details",
            "PRI": "Price details", "APR": "Additional price information",
            "RNG": "Range details", "LOC": "Place/location identification",
            "TOD": "Terms of delivery or transport", "PAC": "Package",
            "PCI": "Package identification", "ALC": "Allowance or charge",
            "RCS": "Requirements and conditions", "UNS": "Section control",
            "CNT": "Control total", "UNT": "Message trailer",
            "UNZ": "Interchange trailer", "FTX": "Free text",
            "FII": "Financial institution information", "MEA": "Measurements",
            "PAI": "Payment instructions"
        }
        
        for segment_code, segment_data in self.segments_dict.items():
            if segment_data.get("description"):
                segment_data["description"] = self.clean_description(segment_data["description"])
            if not segment_data.get("description") or segment_data.get("description") in ["0", "1", ""]:
                if segment_code in standard_descriptions:
                    segment_data["description"] = standard_descriptions[segment_code]
        
        print(f"   ✓ Descriptions ajoutées\n")
    
    def get_statistics(self) -> Dict[str, int]:
        """Calcule les statistiques"""
        stats = {
            "segments": len(self.segments_dict),
            "total_elements": 0, "simple_elements": 0, "groups": 0,
            "elements_in_groups": 0, "elements_with_format": 0,
            "elements_with_value": 0, "elements_with_usage": 0
        }
        
        for segment in self.segments_dict.values():
            for elem in segment.get("elements", []):
                stats["total_elements"] += 1
                if "champ" in elem:
                    stats["simple_elements"] += 1
                    if elem.get("format"): stats["elements_with_format"] += 1
                    if elem.get("valeur"): stats["elements_with_value"] += 1
                    if elem.get("usage"): stats["elements_with_usage"] += 1
                elif "groupe" in elem:
                    stats["groups"] += 1
                    for champ in elem.get("champs", []):
                        stats["elements_in_groups"] += 1
                        if champ.get("format"): stats["elements_with_format"] += 1
                        if champ.get("valeur"): stats["elements_with_value"] += 1
                        if champ.get("usage"): stats["elements_with_usage"] += 1
        
        return stats
    
    def save_to_json(self, output_path: str):
        """Sauvegarde au format JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        segments_list = [self.segments_dict[key] for key in sorted(self.segments_dict.keys())]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(segments_list, f, indent=4, ensure_ascii=False)
        
        print(f"✓ Export sauvegardé: {output_file}")


def process_pdf(pdf_path: Path):
    """Traite un fichier PDF avec l'extracteur adaptatif"""
    print(f"\n{'='*70}")
    print(f"TRAITEMENT: {pdf_path.name}")
    print(f"{'='*70}\n")
    
    # Générer le nom de sortie
    json_name = pdf_path.stem.replace(" ", "_").replace("-", "_")
    output_json = f"export/{json_name}.json"
    
    # Extraction
    extractor = AdaptiveEDIExtractor(str(pdf_path))
    segments = extractor.extract_all()
    
    if segments:
        extractor.save_to_json(output_json)
        print(f"\n✅ EXTRACTION TERMINÉE: {output_json}\n")
    else:
        print(f"\n❌ ÉCHEC: {pdf_path.name}\n")


def main():
    """Fonction principale - Extraction générique"""
    import sys
    
    if len(sys.argv) > 1:
        pdf_filename = sys.argv[1]
        pdf_path = Path("schema") / pdf_filename
        if not pdf_path.exists():
            print(f"❌ Fichier introuvable: {pdf_path}")
            return
        process_pdf(pdf_path)
    else:
        # Traiter tous les PDF du dossier
        schema_dir = Path("schema")
        if not schema_dir.exists():
            print(f"❌ Dossier 'schema/' introuvable")
            return
        
        pdf_files = list(schema_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"❌ Aucun PDF dans 'schema/'")
            return
        
        print(f"\n{'='*70}")
        print("FICHIERS PDF DISPONIBLES")
        print(f"{'='*70}")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"{i}. {pdf_file.name}")
        print(f"{'='*70}\n")
        
        try:
            choice = input("Choisissez (numéro) ou Entrée pour TOUS: ").strip()
            if choice == "":
                for pdf_file in pdf_files:
                    process_pdf(pdf_file)
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(pdf_files):
                    process_pdf(pdf_files[idx])
                else:
                    print("❌ Choix invalide")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Annulé")


if __name__ == "__main__":
    main()
