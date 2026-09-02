from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reanBio', '0022_lessonview_track_3d_and_flashcards'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AIFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField(verbose_name='คำถาม')),
                ('answer', models.TextField(verbose_name='คำตอบของ AI')),
                ('is_helpful', models.BooleanField(verbose_name='เป็นประโยชน์หรือไม่ (True=👍, False=👎)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='ให้ feedback เมื่อ')),
                ('lesson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_feedback', to='reanBio.lesson', verbose_name='บทเรียนที่เกี่ยวข้อง (ถ้ามี)')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_feedback', to=settings.AUTH_USER_MODEL, verbose_name='ผู้ใช้งาน')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
