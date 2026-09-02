from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reanBio", "0020_flashcarddeck_flashcard"),
    ]

    operations = [
        # 📌 เลิกจำกัดให้ 1 คนดูได้ 1 แถวต่อบทเรียน เพื่อเก็บประวัติการเข้าชมซ้ำไว้ทั้งหมด
        migrations.AlterUniqueTogether(
            name="lessonview",
            unique_together=set(),
        ),
        # 📌 แต่ละแถวคือการเข้าชม 1 ครั้ง จึงบันทึกแค่ตอนสร้าง ไม่อัปเดตทับตอนเข้าชมซ้ำ
        migrations.AlterField(
            model_name="lessonview",
            name="viewed_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="เข้าชมเมื่อ"),
        ),
    ]
