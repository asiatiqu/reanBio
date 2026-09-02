import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reanBio", "0021_lessonview_keep_full_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="lessonview",
            name="activity_type",
            field=models.CharField(
                choices=[
                    ("lesson", "เปิดบทเรียน"),
                    ("lesson_3d", "เปิดสื่อ 3D Interactive"),
                    ("flashcard_bank", "เล่นการ์ดคำศัพท์ (คลังกลาง)"),
                    ("flashcard_deck", "เปิดชุดการ์ดของฉัน"),
                ],
                default="lesson",
                max_length=20,
                verbose_name="ประเภทกิจกรรม",
            ),
        ),
        migrations.AddField(
            model_name="lessonview",
            name="flashcard_deck",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="views",
                to="reanBio.flashcarddeck",
                verbose_name="ชุดการ์ดที่เข้าชม",
            ),
        ),
        migrations.AddField(
            model_name="lessonview",
            name="label",
            field=models.CharField(
                blank=True,
                default="",
                max_length=200,
                verbose_name="รายละเอียดเพิ่มเติม (เช่น ตัวกรองที่ใช้ หรือชื่อชุดการ์ดสำรอง)",
            ),
        ),
        migrations.AlterField(
            model_name="lessonview",
            name="lesson",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="views",
                to="reanBio.lesson",
                verbose_name="บทเรียนที่เข้าชม",
            ),
        ),
    ]
