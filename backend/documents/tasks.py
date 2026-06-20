import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger('medguard')


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_document_task(self, doc_id: str):
    """
    Celery task: extract text → clean → chunk → embed → store in ChromaDB.
    """
    from core.models import Document
    from core.utils import extract_text, clean_text, chunk_text, add_chunks_to_chroma

    try:
        doc = Document.objects.get(id=doc_id)
        doc.status = Document.Status.PROCESSING
        doc.save(update_fields=['status'])
        logger.info(f"Processing document: {doc.name} (id={doc_id})")

        # 1. Extract text
        file_path = doc.file.path
        raw_text = extract_text(file_path)

        # 2. Clean
        cleaned = clean_text(raw_text)
        if len(cleaned) < 50:
            raise ValueError("Extracted text is too short or empty.")

        # 3. Chunk
        chunks = chunk_text(
            cleaned,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        # 4. Embed + store in ChromaDB
        metadata = {
            'source': doc.name,
            'doc_type': 'hospital_document',
            'hospital_name': doc.hospital_name or 'Unknown',
            'department': doc.department or 'Unknown',
        }
        try:
            count = add_chunks_to_chroma(
                collection_name=settings.CHROMA_DOCUMENTS_COLLECTION,
                chunks=chunks,
                doc_id=str(doc.id),
                doc_metadata=metadata,
                embedding_model=settings.EMBEDDING_MODEL,
            )
            chroma_doc_id = str(doc.id)
            error_message = ''
        except Exception as exc:
            logger.error(f"Chroma indexing failed for document {doc_id}; using file fallback: {exc}")
            count = len(chunks)
            chroma_doc_id = ''
            error_message = f'Chroma indexing failed; file stored and QA fallback is available. {exc}'

        doc.status = Document.Status.INDEXED
        doc.chunk_count = count
        doc.chroma_doc_id = chroma_doc_id
        doc.error_message = error_message
        doc.save(update_fields=['status', 'chunk_count', 'chroma_doc_id', 'error_message'])
        logger.info(f"Document indexed: {doc.name} -> {count} chunks")

    except Document.DoesNotExist:
        logger.error(f"Document {doc_id} not found.")

    except Exception as exc:
        logger.error(f"Failed to process document {doc_id}: {exc}")
        try:
            doc = Document.objects.get(id=doc_id)
            doc.status = Document.Status.ERROR
            doc.error_message = str(exc)
            doc.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
        raise self.retry(exc=exc)
