import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reanBio", "0025_userprofile_student_info"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lessonview",
            name="activity_type",
            field=models.CharField(
                choices=[
                    ("lesson", "เปิดบทเรียน"),
                    ("lesson_3d", "เปิดสื่อ 3D Interactive"),
                    ("flashcard_bank", "เล่นการ์ดคำศัพท์ (คลังกลาง)"),
                    ("flashcard_deck", "เปิดชุดการ์ดของฉัน"),
                    ("classroom_video", "ดูคลิปวิดีโอห้องเรียน"),
                ],
                default="lesson",
                max_length=20,
                verbose_name="ประเภทกิจกรรม",
            ),
        ),
        migrations.AddField(
            model_name="lessonview",
            name="classroom_video",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="views",
                to="reanBio.classroomvideo",
                verbose_name="วิดีโอห้องเรียนที่เข้าชม",
            ),
        ),
    ]
