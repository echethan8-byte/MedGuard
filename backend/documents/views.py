"""
documents/views.py — Document upload, list, detail, delete.
"""
import os
import logging
from django.conf import settings
from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from core.models import Document, AuditLog
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .tasks import process_document_task

logger = logging.getLogger('medguard')


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD for hospital documents."""
    permission_classes = [AllowAny]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    serializer_class = DocumentSerializer

    def get_queryset(self):
        qs = Document.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer

    def create(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            return Response({'error': f'File type {ext} not allowed.'}, status=400)

        doc = Document.objects.create(
            name=file.name,
            file=file,
            doc_type=ext.lstrip('.'),
            file_size=file.size,
            status=Document.Status.PENDING,
            uploaded_by=request.user if request.user.is_authenticated else None,
            hospital_name=serializer.validated_data.get('hospital_name', ''),
            department=serializer.validated_data.get('department', ''),
            notes=serializer.validated_data.get('notes', ''),
        )

        # Queue async processing
        try:
            process_document_task.delay(str(doc.id))
        except Exception as exc:
            logger.error(f"Document indexing failed after upload for doc={doc.id}: {exc}")
        doc.refresh_from_db()

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=AuditLog.Action.UPLOAD,
            description=f'Uploaded document: {doc.name}',
            metadata={'doc_id': str(doc.id), 'file_size': doc.file_size},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        doc = self.get_object()
        # Remove from ChromaDB
        try:
            from core.utils import delete_doc_from_chroma
            delete_doc_from_chroma(settings.CHROMA_DOCUMENTS_COLLECTION, str(doc.id))
        except Exception as e:
            logger.warning(f"Failed to delete from Chroma: {e}")

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=AuditLog.Action.DELETE,
            description=f'Deleted document: {doc.name}',
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def reindex(self, request, pk=None):
        """Force re-index a document."""
        doc = self.get_object()
        doc.status = Document.Status.PENDING
        doc.chunk_count = 0
        doc.error_message = ''
        doc.save()
        process_document_task.delay(str(doc.id))
        return Response({'message': 'Reindexing queued.'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return document statistics."""
        from django.db.models import Count, Sum
        qs = Document.objects.all()
        return Response({
            'total': qs.count(),
            'by_status': dict(qs.values_list('status').annotate(count=Count('id')).values_list('status', 'count')),
            'total_chunks': qs.aggregate(total=Sum('chunk_count'))['total'] or 0,
        })
