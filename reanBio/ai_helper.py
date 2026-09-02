# 📌 ตัวช่วยเรียก Anthropic (Claude) API สำหรับฟีเจอร์ "ถาม AI" ตอบคำถามวิชาชีววิทยาโดยเฉพาะ
#
# ต้องติดตั้งไลบรารีก่อนใช้งาน:  pip install anthropic python-dotenv
# แล้วสมัคร API key ที่ https://console.anthropic.com/ ใส่ไว้ในไฟล์ .env (ห้ามใส่ในโค้ด/commit ขึ้น GitHub)
#
#   ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
#
# ถ้ายังไม่ได้ตั้งค่า API key ฟังก์ชันนี้จะคืนข้อความแจ้งเตือนแทนการเรียก AI จริง
# เพื่อไม่ให้เว็บพังตอนที่ยังไม่ได้สมัคร key

from django.conf import settings

# 📌 จำกัดขอบเขตคำถามให้เป็นเรื่องชีววิทยา/วิทยาศาสตร์ที่เกี่ยวข้องกับหลักสูตรมัธยมปลายเท่านั้น
SYSTEM_PROMPT = (
    "คุณคือผู้ช่วยตอบคำถามวิชาชีววิทยาสำหรับนักเรียนและคุณครูระดับมัธยมปลายในหลักสูตรไทย "
    "ตอบเป็นภาษาไทย กระชับ เข้าใจง่าย ยกตัวอย่างประกอบเมื่อช่วยให้เข้าใจง่ายขึ้น "
    "ตอบเฉพาะคำถามที่เกี่ยวข้องกับชีววิทยาหรือวิทยาศาสตร์ที่เกี่ยวข้องโดยตรงเท่านั้น "
    "ถ้าคำถามไม่เกี่ยวกับชีววิทยา ให้ปฏิเสธอย่างสุภาพและแนะนำให้ถามเรื่องชีววิทยาแทน "
    "ห้ามให้คำแนะนำทางการแพทย์เฉพาะบุคคล (เช่น วินิจฉัยอาการหรือสั่งยา) ให้แนะนำให้ไปพบแพทย์แทนในกรณีนั้น"
)

MAX_QUESTION_LENGTH = 800  # 📌 กันคำถามยาวเกินไป (ทั้งเรื่องค่าใช้จ่าย API และ UX)


class AskAIError(Exception):
    """เกิดข้อผิดพลาดตอนเรียก AI (ยังไม่ได้ตั้งค่า key, เรียกไม่สำเร็จ, ฯลฯ)"""
    pass


def ask_biology_ai(question, lesson=None):
    """ส่งคำถามไปถาม Claude API แล้วคืนคำตอบเป็นข้อความ (string)
    ถ้ามี lesson ระบุมาด้วย จะแนบชื่อ+เนื้อหาบทเรียนนั้นเป็นบริบทให้ AI ตอบให้ตรงกับบทเรียนที่กำลังเปิดอยู่
    โยน AskAIError ถ้าเกิดปัญหา (ยังไม่ตั้งค่า key / เรียก API ไม่สำเร็จ)"""
    question = (question or "").strip()
    if not question:
        raise AskAIError("กรุณาพิมพ์คำถามก่อนส่ง")
    if len(question) > MAX_QUESTION_LENGTH:
        raise AskAIError(f"คำถามยาวเกินไป (จำกัดไม่เกิน {MAX_QUESTION_LENGTH} ตัวอักษร)")

    if not settings.ANTHROPIC_API_KEY:
        raise AskAIError(
            "ยังไม่ได้ตั้งค่า ANTHROPIC_API_KEY ในไฟล์ .env — "
            "ไปสมัคร API key ได้ที่ https://console.anthropic.com/ แล้วใส่ไว้ในไฟล์ .env ก่อนใช้งานฟีเจอร์นี้"
        )

    try:
        import anthropic
    except ImportError:
        raise AskAIError(
            "ยังไม่ได้ติดตั้งไลบรารี anthropic — รันคำสั่ง: pip install anthropic"
        )

    user_message = question
    if lesson is not None:
        # 📌 แนบบริบทบทเรียนปัจจุบัน (ตัดความยาวเนื้อหาไว้ไม่ให้ยาวเกินไป) ให้ AI ตอบให้ตรงประเด็นบทเรียนนี้
        lesson_context = (lesson.content or lesson.description or "")[:4000]
        user_message = (
            f"บริบท: กำลังเรียนบทเรียนเรื่อง \"{lesson.title}\" "
            f"เนื้อหาบทเรียนโดยย่อ: {lesson_context}\n\n"
            f"คำถามของฉัน: {question}"
        )

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text")).strip()
    except Exception as exc:
        raise AskAIError(f"เรียก AI ไม่สำเร็จ: {exc}")
