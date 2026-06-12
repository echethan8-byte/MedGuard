from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.urls import path
from core.models import PolicyCorpusEntry
from rest_framework import serializers


class PolicyCorpusEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyCorpusEntry
        fields = ['id', 'title', 'organization', 'category', 'version',
                  'published_year', 'chunk_count', 'is_active', 'indexed_at']


class CorpusStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from corpus.loader import get_corpus_stats
        stats = get_corpus_stats()
        entries = PolicyCorpusEntry.objects.filter(is_active=True)
        stats['entries'] = PolicyCorpusEntrySerializer(entries, many=True).data
        return Response(stats)


class CorpusReindexView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        from corpus.loader import load_all_corpus
        corpus_dir = request.data.get('corpus_dir')
        overwrite = request.data.get('overwrite', False)
        try:
            results = load_all_corpus(corpus_dir=corpus_dir, overwrite=overwrite)
            return Response(results)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


urlpatterns = [
    path('stats/', CorpusStatsView.as_view(), name='corpus-stats'),
    path('reindex/', CorpusReindexView.as_view(), name='corpus-reindex'),
]
