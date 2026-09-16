from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reanBio", "0027_lesson_content_ch1_biology_intro"),
    ]

    operations = [
        migrations.AddField(
            model_name="lesson",
            name="subject",
            field=models.CharField(
                choices=[
                    ("bio", "ชีววิทยา"),
                    ("english", "ภาษาอังกฤษ"),
                ],
                default="bio",
                max_length=10,
                verbose_name="รายวิชา",
            ),
        ),
    ]
