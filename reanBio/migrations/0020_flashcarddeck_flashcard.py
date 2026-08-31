import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("reanBio", "0019_classroom_quiz_attempt_student_info_and_limit"),
    ]

    operations = [
        migrations.CreateModel(
            name="FlashcardDeck",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="ชื่อชุดการ์ด")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="flashcard_decks", to=settings.AUTH_USER_MODEL, verbose_name="เจ้าของ")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Flashcard",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("front", models.TextField(verbose_name="คำถาม/คำศัพท์ (ด้านหน้า)")),
                ("back", models.TextField(verbose_name="คำตอบ/ความหมาย (ด้านหลัง)")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="ลำดับ")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("deck", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cards", to="reanBio.flashcarddeck", verbose_name="ชุดการ์ด")),
            ],
            options={
                "ordering": ["deck", "order", "created_at"],
            },
        ),
    ]
