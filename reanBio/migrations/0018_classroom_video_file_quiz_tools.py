import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("reanBio", "0017_add_lesson_credit_weight_and_backfill"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClassroomVideo",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="ชื่อคลิป")),
                ("youtube_url", models.URLField(blank=True, default="", verbose_name="ลิงก์ YouTube")),
                ("video_file", models.FileField(blank=True, null=True, upload_to="classroom_videos/%Y/%m/", verbose_name="ไฟล์วิดีโอ")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("added_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="ผู้เพิ่ม")),
                ("classroom", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="videos", to="reanBio.classroom", verbose_name="ห้องเรียน")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ClassroomFile",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="ชื่อเอกสาร")),
                ("file", models.FileField(upload_to="classroom_files/%Y/%m/", verbose_name="ไฟล์เอกสาร")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("added_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="ผู้อัปโหลด")),
                ("classroom", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="files", to="reanBio.classroom", verbose_name="ห้องเรียน")),
            ],
            options={
                "ordering": ["-uploaded_at"],
            },
        ),
        migrations.CreateModel(
            name="ClassroomQuiz",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="ชื่อแบบทดสอบ")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("classroom", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quizzes", to="reanBio.classroom", verbose_name="ห้องเรียน")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="ผู้สร้าง")),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name_plural": "Classroom quizzes",
            },
        ),
        migrations.CreateModel(
            name="ClassroomQuizQuestion",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="ลำดับข้อ")),
                ("question_type", models.CharField(choices=[("mcq", "ปรนัย (เลือกคำตอบ)"), ("text", "อัตนัย (พิมพ์คำตอบ)")], default="mcq", max_length=4, verbose_name="ประเภทคำถาม")),
                ("text", models.TextField(verbose_name="โจทย์คำถาม")),
                ("points", models.PositiveIntegerField(default=1, verbose_name="คะแนนเต็มของข้อนี้")),
                ("accepted_answers", models.JSONField(blank=True, default=list, verbose_name="คำตอบที่ยอมรับ (อัตนัย)")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="reanBio.classroomquiz", verbose_name="แบบทดสอบ")),
            ],
            options={
                "ordering": ["quiz", "order"],
            },
        ),
        migrations.CreateModel(
            name="ClassroomQuizChoice",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(default=1)),
                ("text", models.CharField(max_length=500, verbose_name="ข้อความตัวเลือก")),
                ("is_correct", models.BooleanField(default=False, verbose_name="เป็นคำตอบที่ถูกต้อง")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="reanBio.classroomquizquestion", verbose_name="คำถาม")),
            ],
            options={
                "ordering": ["question", "order"],
            },
        ),
        migrations.CreateModel(
            name="ClassroomQuizAttempt",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.FloatField(default=0, verbose_name="คะแนนที่ได้")),
                ("max_score", models.FloatField(default=0, verbose_name="คะแนนเต็ม")),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True, verbose_name="เวลาที่ส่งคำตอบ")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="reanBio.classroomquiz", verbose_name="แบบทดสอบ")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="classroom_quiz_attempts", to=settings.AUTH_USER_MODEL, verbose_name="ผู้ทำ")),
            ],
            options={
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="ClassroomQuizAnswer",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="ลำดับที่แสดงในการทำครั้งนี้")),
                ("text_answer", models.TextField(blank=True, default="", verbose_name="คำตอบที่พิมพ์")),
                ("is_correct", models.BooleanField(default=False, verbose_name="ตอบถูกหรือไม่")),
                ("points_earned", models.FloatField(default=0, verbose_name="คะแนนที่ได้ในข้อนี้")),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="reanBio.classroomquizattempt", verbose_name="การทำแบบทดสอบ")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempt_answers", to="reanBio.classroomquizquestion", verbose_name="คำถาม")),
                ("selected_choice", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="reanBio.classroomquizchoice", verbose_name="ตัวเลือกที่เลือก")),
            ],
            options={
                "ordering": ["attempt", "order"],
            },
        ),
    ]
