"""
Script de traitement en masse de tous les PDF EDI
"""

from pathlib import Path
import sys
import time

# Importer l'extracteur
sys.path.insert(0, str(Path(__file__).parent))
from extract_edi_adaptive import AdaptiveEDIExtractor, process_pdf


def process_all_pdfs():
    """Traite tous les PDF du dossier schema/"""
    
    schema_dir = Path("schema")
    if not schema_dir.exists():
        print(f"❌ Dossier 'schema/' introuvable")
        return
    
    pdf_files = list(schema_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ Aucun PDF trouvé dans 'schema/'")
        return
    
    print(f"\n{'='*70}")
    print(f"TRAITEMENT EN MASSE - {len(pdf_files)} FICHIERS PDF")
    print(f"{'='*70}\n")
    
    results = []
    start_time = time.time()
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] Traitement de {pdf_file.name}...")
        
        try:
            pdf_start = time.time()
            process_pdf(pdf_file)
            pdf_duration = time.time() - pdf_start
            
            results.append({
                'file': pdf_file.name,
                'status': 'SUCCESS',
                'duration': pdf_duration
            })
        except Exception as e:
            print(f"❌ ERREUR: {str(e)}")
            results.append({
                'file': pdf_file.name,
                'status': 'FAILED',
                'error': str(e)
            })
    
    total_duration = time.time() - start_time
    
    # Résumé
    print(f"\n\n{'='*70}")
    print("RÉSUMÉ DU TRAITEMENT EN MASSE")
    print(f"{'='*70}\n")
    
    success_count = len([r for r in results if r['status'] == 'SUCCESS'])
    failed_count = len([r for r in results if r['status'] == 'FAILED'])
    
    print(f"Fichiers traités  : {len(results)}")
    print(f"Succès           : {success_count}")
    print(f"Échecs           : {failed_count}")
    print(f"Durée totale     : {total_duration:.2f}s")
    print(f"Durée moyenne    : {total_duration/len(results):.2f}s/fichier\n")
    
    if failed_count > 0:
        print("FICHIERS EN ÉCHEC:")
        for result in results:
            if result['status'] == 'FAILED':
                print(f"  ❌ {result['file']}: {result.get('error', 'Unknown error')}")
        print()
    
    print("FICHIERS RÉUSSIS:")
    for result in results:
        if result['status'] == 'SUCCESS':
            print(f"  ✅ {result['file']} ({result['duration']:.2f}s)")
    
    print(f"\n{'='*70}")
    print(f"✅ TRAITEMENT TERMINÉ: {success_count}/{len(results)} fichiers extraits")
    print(f"{'='*70}\n")


def main():
    """Fonction principale"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        process_all_pdfs()
    else:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                 EXTRACTEUR EDI - TRAITEMENT EN MASSE                 ║
╚══════════════════════════════════════════════════════════════════════╝

Ce script va traiter TOUS les fichiers PDF du dossier 'schema/' et
générer les fichiers JSON correspondants dans 'export/'.

Appuyez sur Entrée pour continuer ou Ctrl+C pour annuler...
        """)
        
        try:
            input()
            process_all_pdfs()
        except KeyboardInterrupt:
            print("\n\n❌ Traitement annulé par l'utilisateur\n")


if __name__ == "__main__":
    main()
