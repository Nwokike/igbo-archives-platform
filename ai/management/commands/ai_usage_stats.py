"""
Management command to show AI usage statistics.
Useful for capacity planning and monitoring.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ai.models import ChatMessage, ArchiveAnalysis
from django.db.models import Count, Q


class Command(BaseCommand):
    help = 'Display AI usage statistics for monitoring and capacity planning'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timedelta(days=days)
        
        self.stdout.write(self.style.SUCCESS(f'\nAI Usage Statistics (Last {days} days)\n'))
        self.stdout.write('=' * 60)
        
        # Chat usage
        chat_messages = ChatMessage.objects.filter(
            created_at__gte=cutoff,
            role='assistant'
        )
        chat_count = chat_messages.count()
        unique_sessions = chat_messages.values('session').distinct().count()
        unique_users = chat_messages.values('session__user').distinct().count()
        
        self.stdout.write(f'\n� Chat Usage:')
        self.stdout.write(f'  Total AI responses: {chat_count}')
        self.stdout.write(f'  Unique sessions: {unique_sessions}')
        self.stdout.write(f'  Unique users: {unique_users}')
        
        # Model breakdown
        model_usage = chat_messages.values('model_used').annotate(
            count=Count('id')
        ).order_by('-count')
        
        if model_usage:
            self.stdout.write(f'\n  Model breakdown:')
            for item in model_usage:
                model = item['model_used'] or 'unknown'
                count = item['count']
                self.stdout.write(f'    {model}: {count}')
        
        # Vision/Analysis usage
        analyses = ArchiveAnalysis.objects.filter(created_at__gte=cutoff)
        analysis_count = analyses.count()
        unique_archives = analyses.values('archive').distinct().count()
        unique_users_vision = analyses.values('user').distinct().count()
        
        self.stdout.write(f'\n🔍 Image Analysis Usage:')
        self.stdout.write(f'  Total analyses: {analysis_count}')
        self.stdout.write(f'  Unique archives analyzed: {unique_archives}')
        self.stdout.write(f'  Unique users: {unique_users_vision}')
        
        # Analysis type breakdown
        type_usage = analyses.values('analysis_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        if type_usage:
            self.stdout.write(f'\n  Analysis type breakdown:')
            for item in type_usage:
                analysis_type = item['analysis_type'] or 'unknown'
                count = item['count']
                self.stdout.write(f'    {analysis_type}: {count}')
        
        # TTS/STT usage (approximate from rate limit cache keys)
        from django.core.cache import cache
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        tts_count = 0
        stt_count = 0
        
        # Estimate from cache keys (not perfect but gives rough idea)
        for user in User.objects.all():
            tts_key = f'ai_tts_{user.id}'
            stt_key = f'ai_stt_{user.id}'
            if cache.get(tts_key, 0) > 0:
                tts_count += cache.get(tts_key, 0)
            if cache.get(stt_key, 0) > 0:
                stt_count += cache.get(stt_key, 0)
        
        self.stdout.write(f'\n🎤 TTS/STT Usage (estimated):')
        self.stdout.write(f'  TTS requests: ~{tts_count}')
        self.stdout.write(f'  STT requests: ~{stt_count}')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('\nStatistics complete.\n'))
