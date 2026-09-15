from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reanBio', '0024_knowledgedocument'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='full_name',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='ชื่อ-นามสกุล (สำหรับห้องเรียน)'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='student_class',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='ชั้น (สำหรับห้องเรียน)'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='student_number',
            field=models.CharField(blank=True, default='', max_length=10, verbose_name='เลขที่ (สำหรับห้องเรียน)'),
        ),
    ]
