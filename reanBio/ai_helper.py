# 📌 ตัวช่วยเรียก Anthropic (Claude) API สำหรับฟีเจอร์ "ถาม AI" ตอบคำถามวิชาชีววิทยาโดยเฉพาะ
#
# ต้องติดตั้งไลบรารีก่อนใช้งาน:  pip install anthropic python-dotenv
# แล้วสมัคร API key ที่ https://console.anthropic.com/ ใส่ไว้ในไฟล์ .env (ห้ามใส่ในโค้ด/commit ขึ้น GitHub)
#
#   ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
#
# ถ้ายังไม่ได้ตั้งค่า API key ฟังก์ชันนี้จะคืนข้อความแจ้งเตือนแทนการเรียก AI จริง
# เพื่อไม่ให้เว็บพังตอนที่ยังไม่ได้สมัคร key

import re

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


# 📌 ระบบค้นหาบริบทที่เกี่ยวข้อง (RAG แบบง่าย) — ค้นจากเนื้อหาบทเรียนทั้งหมดในระบบ ไม่ใช่แค่บทที่กำลังเปิดอยู่
# ใช้วิธีเทียบ character n-gram overlap แทนการใช้ embedding model เพราะข้อความเป็นภาษาไทย (ไม่มีช่องว่างแบ่งคำ)
# และคลังเนื้อหาตอนนี้มีขนาดเล็ก จึงไม่จำเป็นต้องพึ่งไลบรารีหรือฐานข้อมูลเวกเตอร์เพิ่มเติม
RAG_NGRAM_SIZE = 4  # 📌 ใช้ 4 ตัวอักษรแทน 3 เพื่อลดโอกาส "บังเอิญ" ตรงกันจากคำศัพท์ภาษาอังกฤษสั้นๆ ที่ปนอยู่ในเนื้อหา (เช่น DNA, cell)
RAG_TOP_K = 3  # 📌 ตอนนี้ค้นทั้งบทเรียนและเอกสาร PDF อ้างอิงรวมกัน เลยเผื่อที่ให้ผสมกันได้มากกว่าตอนค้นแค่บทเรียนอย่างเดียว
RAG_CHUNK_CHARS = 1500
RAG_MIN_SCORE = 0.15  # 📌 กันไม่ให้ดึงบทเรียนที่ไม่เกี่ยวข้องเลยมาแนบให้ AI อ่านฟรีๆ
RAG_MIN_OVERLAP = 3  # 📌 ต้องมีจำนวนตัวอักษรที่ตรงกันจริงขั้นต่ำด้วย ไม่ใช่แค่สัดส่วนสูง (กันคำถามสั้นๆ หลอกคะแนน)


def _char_ngrams(text, n=RAG_NGRAM_SIZE):
    cleaned = re.sub(r'\s+', '', text or '')
    if len(cleaned) < n:
        return {cleaned} if cleaned else set()
    return {cleaned[i:i + n] for i in range(len(cleaned) - n + 1)}


def _similarity_score(question_grams, text):
    text_grams = _char_ngrams(text)
    if not question_grams or not text_grams:
        return 0.0
    overlap = len(question_grams & text_grams)
    if overlap < RAG_MIN_OVERLAP:
        return 0.0
    return overlap / len(question_grams)


def _iter_knowledge_sources(exclude_lesson_pk=None):
    """ไล่คืนแหล่งข้อมูลทั้งหมดที่ใช้เป็นคลังค้นหาสำหรับ RAG: บทเรียนทุกบท + เอกสาร PDF ที่แอดมินอัปโหลด (คลังกลาง)
    คืนเป็น tuple (label, text) ทีละรายการ"""
    from .models import Lesson, KnowledgeDocument  # 📌 import แบบ local กันปัญหา circular import กับ models.py

    lessons_qs = Lesson.objects.all()
    if exclude_lesson_pk:
        lessons_qs = lessons_qs.exclude(pk=exclude_lesson_pk)
    for lesson_obj in lessons_qs:
        text = f"{lesson_obj.title} {lesson_obj.description} {lesson_obj.content}"
        yield (f"บทเรียนที่เกี่ยวข้องในระบบ: {lesson_obj.title}", text)

    for doc in KnowledgeDocument.objects.exclude(extracted_text=""):
        text = f"{doc.title} {doc.extracted_text}"
        yield (f"เอกสารอ้างอิงที่เกี่ยวข้อง: {doc.title}", text)


def _retrieve_relevant_context(question, exclude_lesson_pk=None, top_k=RAG_TOP_K):
    """ค้นหาบทเรียน/เอกสารอ้างอิงที่เนื้อหาใกล้เคียงกับคำถามมากที่สุด คืนเป็นลิสต์ของ (label, text) เรียงจากเกี่ยวข้องมากไปน้อย"""
    question_grams = _char_ngrams(question)
    if not question_grams:
        return []

    scored = []
    for label, text in _iter_knowledge_sources(exclude_lesson_pk=exclude_lesson_pk):
        score = _similarity_score(question_grams, text)
        if score >= RAG_MIN_SCORE:
            scored.append((score, label, text))

    scored.sort(key=lambda triple: triple[0], reverse=True)
    return [(label, text) for _, label, text in scored[:top_k]]


def extract_pdf_text(file_path, max_chars=200000):
    """แกะข้อความจากไฟล์ PDF ด้วยไลบรารี pypdf คืนเป็น string (อาจได้ข้อความว่างถ้าเป็น PDF ที่สแกนมาแบบไม่มีเลเยอร์ข้อความ)
    ใช้ตอนแอดมินอัปโหลดเอกสารอ้างอิงในหน้า Admin — โยน AskAIError ถ้าแกะไม่สำเร็จ"""
    try:
        import pypdf
    except ImportError:
        raise AskAIError("ยังไม่ได้ติดตั้งไลบรารี pypdf — รันคำสั่ง: pip install pypdf")

    try:
        reader = pypdf.PdfReader(file_path)
        pages_text = [(page.extract_text() or "") for page in reader.pages]
        return "\n\n".join(pages_text).strip()[:max_chars]
    except Exception as exc:
        raise AskAIError(f"แกะข้อความจากไฟล์ PDF ไม่สำเร็จ: {exc}")


def ask_biology_ai(question, lesson=None):
    """ส่งคำถามไปถาม Claude API แล้วคืนคำตอบเป็นข้อความ (string)
    ถ้ามี lesson ระบุมาด้วย จะแนบชื่อ+เนื้อหาบทเรียนนั้นเป็นบริบทหลัก
    นอกจากนี้จะค้นหาบทเรียนอื่นในระบบที่เนื้อหาเกี่ยวข้องกับคำถามมาแนบเพิ่มด้วย (RAG แบบง่าย)
    เพื่อให้ AI ตอบโดยอิงเนื้อหาที่สอนจริงในเว็บ ไม่ใช่แค่ความรู้ทั่วไปของโมเดล
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

    context_blocks = []
    if lesson is not None:
        # 📌 แนบบริบทบทเรียนปัจจุบัน (ตัดความยาวเนื้อหาไว้ไม่ให้ยาวเกินไป) ให้ AI ตอบให้ตรงประเด็นบทเรียนนี้
        lesson_context = (lesson.content or lesson.description or "")[:4000]
        context_blocks.append(f"[บทเรียนที่กำลังเปิดอยู่: {lesson.title}]\n{lesson_context}")

    try:
        related_sources = _retrieve_relevant_context(question, exclude_lesson_pk=lesson.pk if lesson is not None else None)
        for label, related_text in related_sources:
            context_blocks.append(f"[{label}]\n{related_text[:RAG_CHUNK_CHARS]}")
    except Exception:
        # 📌 ถ้าการค้นหาบริบทเพิ่มเติมมีปัญหา ไม่ควรทำให้ทั้งฟีเจอร์ล่ม แค่ข้ามส่วนนี้ไปแล้วตอบโดยไม่มีบริบทเสริม
        pass

    user_message = question
    if context_blocks:
        joined_context = "\n\n".join(context_blocks)
        user_message = (
            f"บริบทเนื้อหาชีวะจากบทเรียน/เอกสารอ้างอิงในระบบที่อาจเกี่ยวข้องกับคำถาม "
            f"(ใช้ประกอบการตอบถ้าเกี่ยวข้องจริง ถ้าไม่เกี่ยวก็ไม่ต้องอ้างอิงถึง):\n\n{joined_context}\n\n"
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
