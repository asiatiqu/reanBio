from collections import Counter

from django.db import migrations, models

# 📌 เพิ่มฟิลด์ "น้ำหนักคะแนน" (credit_weight) ให้ Lesson เพื่อใช้คำนวณคะแนนรวมถ่วงน้ำหนักแบบ GPA ในแดชบอร์ด
# (แต่ละหัวข้อย่อยมีน้ำหนักไม่เท่ากัน เหมือนวิชาที่หน่วยกิตไม่เท่ากัน)
#
# น้ำหนักที่กำหนดด้านล่างอิงจากความถี่/รูปแบบที่มักพบในข้อสอบ A-Level ชีววิทยา (ประเมินจากความรู้ทั่วไป
# เกี่ยวกับแนวข้อสอบ ไม่ใช่ตัวเลขทางการจากคลังข้อสอบจริง จึงเป็นค่าตั้งต้นที่ปรับได้ภายหลังผ่านฟิลด์นี้):
#   1.1 ธรรมชาติของสิ่งมีชีวิต       -> เนื้อหาเชิงนิยาม ออกไม่บ่อยนัก                      -> น้ำหนัก 1.0
#   1.2 วิธีการทางวิทยาศาสตร์        -> มักออกเป็นโจทย์วิเคราะห์ข้อมูล/ตัวแปรการทดลอง ซึ่ง
#                                        เป็นสไตล์ที่ A-Level ชีววิทยาออกบ่อยและถ่วงน้ำหนักสูง -> น้ำหนัก 1.5
#   1.3 สะเต็มศึกษาฯ                 -> แทบไม่ปรากฏโดยตรงในข้อสอบ A-Level ชีววิทยา          -> น้ำหนัก 0.5
#
# นอกจากนี้ยัง backfill ฟิลด์ Attempt.lesson ของ "ข้อสอบ" (mode='exam') รุ่นเก่าที่เคยสุ่มคำถามจากทั้งบท
# (ตอนนั้นยังไม่ผูกกับบทเรียนเดียว จึง lesson=None) ให้ชี้ไปยังบทเรียนที่มีคำถามถูกสุ่มมาทำมากที่สุดในการทำครั้งนั้น
# เพื่อให้ประวัติเก่ายังคงแสดงผลถูกต้องหลังจากเปลี่ยนให้ข้อสอบผูกกับบทเรียน (หัวข้อย่อย) เดียวแทนทั้งบท

CREDIT_WEIGHTS = {
    "1.1": 1.0,
    "1.2": 1.5,
    "1.3": 0.5,
}


def set_credit_weights(apps, schema_editor):
    Lesson = apps.get_model("reanBio", "Lesson")
    for code, weight in CREDIT_WEIGHTS.items():
        Lesson.objects.filter(subtopic_code=code).update(credit_weight=weight)


def reverse_credit_weights(apps, schema_editor):
    Lesson = apps.get_model("reanBio", "Lesson")
    for code in CREDIT_WEIGHTS:
        Lesson.objects.filter(subtopic_code=code).update(credit_weight=1.0)


def backfill_exam_lesson(apps, schema_editor):
    Attempt = apps.get_model("reanBio", "Attempt")
    AttemptAnswer = apps.get_model("reanBio", "AttemptAnswer")

    orphan_exams = Attempt.objects.filter(mode="exam", lesson__isnull=True)
    for attempt in orphan_exams:
        lesson_ids = list(
            AttemptAnswer.objects.filter(attempt=attempt)
            .exclude(question__lesson__isnull=True)
            .values_list("question__lesson_id", flat=True)
        )
        if not lesson_ids:
            continue
        most_common_lesson_id, _ = Counter(lesson_ids).most_common(1)[0]
        attempt.lesson_id = most_common_lesson_id
        attempt.save(update_fields=["lesson"])


def reverse_backfill_exam_lesson(apps, schema_editor):
    # หมายเหตุ: ไม่ย้อนคืน เพราะไม่สามารถแยกแยะได้ว่า Attempt ใดถูก backfill โดย migration นี้
    # กับ Attempt ใหม่ที่ถูกสร้างขึ้นตามปกติหลังจากนี้ (ทั้งคู่มี lesson ตั้งไว้เหมือนกัน)
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("reanBio", "0016_add_hooks_analogies_mindmaps"),
    ]

    operations = [
        migrations.AddField(
            model_name="lesson",
            name="credit_weight",
            field=models.FloatField(
                default=1.0, verbose_name="น้ำหนักคะแนน (เหมือนหน่วยกิต)"
            ),
        ),
        migrations.RunPython(set_credit_weights, reverse_credit_weights),
        migrations.RunPython(backfill_exam_lesson, reverse_backfill_exam_lesson),
    ]
