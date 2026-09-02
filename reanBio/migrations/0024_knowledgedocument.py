from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reanBio', '0023_aifeedback'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='KnowledgeDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='ชื่อเอกสาร')),
                ('file', models.FileField(upload_to='knowledge_docs/%Y/%m/', verbose_name='ไฟล์ PDF')),
                ('extracted_text', models.TextField(blank=True, default='', verbose_name='เนื้อหาที่แกะจากไฟล์ (ระบบสร้างให้อัตโนมัติตอนอัปโหลด)')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='อัปโหลดเมื่อ')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='knowledge_documents', to=settings.AUTH_USER_MODEL, verbose_name='ผู้อัปโหลด')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
