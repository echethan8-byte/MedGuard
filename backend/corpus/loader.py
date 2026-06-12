"""
corpus/loader.py — Scripts to load the healthcare policy corpus into ChromaDB.
Run: python manage.py shell -c "from corpus.loader import load_all_corpus; load_all_corpus()"
Or: python manage.py load_corpus
"""
import glob
import os
import logging
from pathlib import Path
from django.conf import settings
from core.utils import extract_text, clean_text, chunk_text, add_chunks_to_chroma
from core.models import PolicyCorpusEntry

logger = logging.getLogger('medguard')

# Policy sources with metadata
POLICY_SOURCES = [
    {
        "organization": "WHO",
        "title": "WHO Guidelines on Hand Hygiene in Health Care",
        "category": "Infection Control",
        "version": "2022",
        "year": 2022,
        "filename": "WHO_Hand_Hygiene_Guidelines_2022.pdf",
        "url": "https://www.who.int/docs/default-source/infection-prevention-and-control/hand-hygiene.pdf",
    },
    {
        "organization": "WHO",
        "title": "WHO Core Components of Infection Prevention and Control",
        "category": "Infection Control",
        "version": "2016",
        "year": 2016,
        "filename": "WHO_IPC_Core_Components_2016.pdf",
        "url": "https://www.who.int/infection-prevention/publications/ipc-components-guidelines/en/",
    },
    {
        "organization": "CDC",
        "title": "CDC NHSN Patient Safety Component Manual",
        "category": "HAI Prevention",
        "version": "2024",
        "year": 2024,
        "filename": "CDC_NHSN_PSC_Manual_2024.pdf",
        "url": "https://www.cdc.gov/nhsn/pdfs/pscmanual/pcsmanual_current.pdf",
    },
    {
        "organization": "CDC",
        "title": "CDC Guidelines for Prevention of Healthcare-Associated Pneumonia",
        "category": "HAI Prevention",
        "version": "2022",
        "year": 2022,
        "filename": "CDC_HAP_Prevention_Guidelines.pdf",
        "url": "https://www.cdc.gov/infectioncontrol/pdf/guidelines/healthcare-pneumonia-guidelines-H.pdf",
    },
    {
        "organization": "CDC",
        "title": "CDC Management of Multidrug-Resistant Organisms",
        "category": "MDRO Control",
        "version": "2023",
        "year": 2023,
        "filename": "CDC_MDRO_Management_2023.pdf",
        "url": "https://www.cdc.gov/hicpac/pdf/guidelines/MDROGuideline2006.pdf",
    },
    {
        "organization": "OSHA",
        "title": "Bloodborne Pathogens Standard 29 CFR 1910.1030",
        "category": "Occupational Safety",
        "version": "2023",
        "year": 2023,
        "filename": "OSHA_Bloodborne_Pathogens_1910_1030.pdf",
        "url": "https://www.osha.gov/bloodborne-pathogens/standards",
    },
    {
        "organization": "HHS",
        "title": "HHS Hospital-Acquired Condition Reduction Program",
        "category": "HAI Prevention",
        "version": "2023",
        "year": 2023,
        "filename": "HHS_HACRP_2023.pdf",
        "url": "https://www.cms.gov/Medicare/Medicare-Fee-for-Service-Payment/AcuteInpatientPPS/HAC-Reduction-Program",
    },
    {
        "organization": "TJC",
        "title": "The Joint Commission Infection Control Standards",
        "category": "Infection Control",
        "version": "2024",
        "year": 2024,
        "filename": "TJC_IC_Standards_2024.pdf",
        "url": "https://www.jointcommission.org/standards/standard-faqs/hospital/infection-control-ic/",
    },
    {
        "organization": "AHRQ",
        "title": "AHRQ Comprehensive Unit-based Safety Program Toolkit",
        "category": "Patient Safety",
        "version": "2023",
        "year": 2023,
        "filename": "AHRQ_CUSP_Toolkit.pdf",
        "url": "https://www.ahrq.gov/sites/default/files/wysiwyg/hai/cusp/resources/cusp-toolkit.pdf",
    },
]


def index_policy_file(
    file_path: str,
    source_meta: dict,
    overwrite: bool = False,
) -> int:
    """
    Load a single policy PDF into the ChromaDB policy corpus.
    Returns number of chunks indexed.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return 0

    # Check if already indexed
    existing = PolicyCorpusEntry.objects.filter(source_file=source_meta['filename'], is_active=True).first()
    if existing and not overwrite:
        logger.info(f"Already indexed: {source_meta['filename']} ({existing.chunk_count} chunks)")
        return existing.chunk_count

    logger.info(f"Indexing: {source_meta['filename']}")

    # Extract + clean + chunk
    raw_text = extract_text(file_path)
    cleaned = clean_text(raw_text)
    chunks = chunk_text(cleaned, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

    # Build metadata for each chunk
    chunk_metadata = {
        "source": source_meta['filename'],
        "organization": source_meta['organization'],
        "category": source_meta['category'],
        "doc_type": "policy",
        "year": str(source_meta.get('year', '')),
    }

    doc_id = f"policy_{source_meta['organization']}_{source_meta['filename']}"
    count = add_chunks_to_chroma(
        collection_name=settings.CHROMA_POLICY_COLLECTION,
        chunks=chunks,
        doc_id=doc_id,
        doc_metadata=chunk_metadata,
        embedding_model=settings.EMBEDDING_MODEL,
    )

    # Save/update DB record
    PolicyCorpusEntry.objects.update_or_create(
        source_file=source_meta['filename'],
        defaults={
            'title': source_meta['title'],
            'organization': source_meta['organization'],
            'version': source_meta.get('version', ''),
            'published_year': source_meta.get('year'),
            'category': source_meta.get('category', ''),
            'chunk_count': count,
            'is_active': True,
        }
    )
    logger.info(f"Indexed: {source_meta['filename']} → {count} chunks")
    return count


def get_source_meta(file_path: str) -> dict:
    """Return metadata for a PDF, using POLICY_SOURCES when available."""
    filename = os.path.basename(file_path)
    for source in POLICY_SOURCES:
        if source['filename'] == filename:
            return source

    title = Path(filename).stem.replace('_', ' ').replace('-', ' ').strip()
    title = title.title() if title else filename
    return {
        'organization': 'PE',
        'title': title,
        'category': 'Physical Exam',
        'version': '',
        'year': None,
        'filename': filename,
    }


def load_all_corpus(corpus_dir: str = None, overwrite: bool = False) -> dict:
    """
    Load all policy documents from corpus_dir.
    Expected directory structure: corpus_dir/<filename>.pdf
    """
    if corpus_dir is None:
        corpus_dir = os.path.join(settings.BASE_DIR, 'corpus', 'policies')

    os.makedirs(corpus_dir, exist_ok=True)

    results = {'indexed': 0, 'skipped': 0, 'errors': 0, 'total_chunks': 0}
    pdf_files = sorted(glob.glob(os.path.join(corpus_dir, '*.pdf')))

    for file_path in pdf_files:
        source_meta = get_source_meta(file_path)
        try:
            count = index_policy_file(file_path, source_meta, overwrite=overwrite)
            if count > 0:
                results['indexed'] += 1
                results['total_chunks'] += count
            else:
                results['skipped'] += 1
        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
            results['errors'] += 1

    logger.info(f"Corpus load complete: {results}")
    return results


def get_corpus_stats() -> dict:
    """Return statistics about the loaded policy corpus."""
    from django.db.models import Sum, Count
    entries = PolicyCorpusEntry.objects.filter(is_active=True)
    return {
        'total_documents': entries.count(),
        'total_chunks': entries.aggregate(total=Sum('chunk_count'))['total'] or 0,
        'by_organization': list(
            entries.values('organization').annotate(
                docs=Count('id'), chunks=Sum('chunk_count')
            )
        ),
    }
