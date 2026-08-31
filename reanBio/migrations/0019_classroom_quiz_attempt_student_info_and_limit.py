from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reanBio", "0018_classroom_video_file_quiz_tools"),
    ]

    operations = [
        migrations.AddField(
            model_name="classroomquizattempt",
            name="student_name",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="ชื่อ-นามสกุล"),
        ),
        migrations.AddField(
            model_name="classroomquizattempt",
            name="student_class",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="ชั้น"),
        ),
        migrations.AddField(
            model_name="classroomquizattempt",
            name="student_number",
            field=models.CharField(blank=True, default="", max_length=10, verbose_name="เลขที่"),
        ),
        migrations.AlterModelOptions(
            name="classroomquizattempt",
            options={"ordering": ["-started_at"]},
        ),
        migrations.AlterUniqueTogether(
            name="classroomquizattempt",
            unique_together={("quiz", "user")},
        ),
    ]
