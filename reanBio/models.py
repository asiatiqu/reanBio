import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# 📌 1. Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'นักเรียน'),
        ('teacher', 'คุณครู'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', verbose_name="บทบาท") 

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='reanbio_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='reanbio_user_permissions_set',
        related_query_name='user',
    )

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def is_student(self):
        return self.role == 'student'


# 📌 2. UserProfile Model
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='userprofile',
        verbose_name="ผู้ใช้งาน"
    )
    grade = models.CharField(max_length=100, verbose_name="ระดับชั้น", blank=True, null=True)

    # 📌 ข้อมูลนักเรียนสำหรับห้องเรียน/แบบทดสอบ (ชื่อ-นามสกุล/ชั้น/เลขที่) กรอกครั้งเดียวตอนเข้าห้องเรียนครั้งแรก
    # แล้วใช้ซ้ำได้ทุกแบบทดสอบ ไม่ต้องกรอกซ้ำทุกครั้งที่ทำข้อสอบ
    full_name = models.CharField(max_length=200, blank=True, default="", verbose_name="ชื่อ-นามสกุล (สำหรับห้องเรียน)")
    student_class = models.CharField(max_length=50, blank=True, default="", verbose_name="ชั้น (สำหรับห้องเรียน)")
    student_number = models.CharField(max_length=10, blank=True, default="", verbose_name="เลขที่ (สำหรับห้องเรียน)")

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def has_student_info(self):
        return bool(self.full_name and self.student_class and self.student_number)


# 📌 3. Helper & Classroom Model
def generate_classroom_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class Classroom(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อห้องเรียน")
    code = models.CharField(max_length=6, unique=True, default=generate_classroom_code, verbose_name="รหัสห้องเรียน")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_classrooms', verbose_name="คุณครูผู้สอน")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_classrooms', blank=True, verbose_name="นักเรียน")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Lesson(models.Model):
    GRADE_CHOICES = (
        ('m4', 'ม.4'),
        ('m5', 'ม.5'),
        ('m6', 'ม.6'),
    )

    title = models.CharField(max_length=200, verbose_name="ชื่อบทเรียน")
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, verbose_name="ระดับชั้น")
    icon = models.CharField(max_length=10, default="🧬", verbose_name="อีโมจิประจำบท")
    description = models.TextField(verbose_name="คำอธิบายย่อย")
    content = models.TextField(blank=True, default="", verbose_name="เนื้อหาบทเรียนแบบเต็ม")
    diagram_svg = models.TextField(blank=True, default="", verbose_name="ภาพประกอบ (SVG)")
    chapter = models.PositiveIntegerField(default=1, verbose_name="บทที่ (ตามหนังสือเรียน)")
    chapter_title = models.CharField(max_length=200, blank=True, default="", verbose_name="ชื่อบทใหญ่")
    subtopic_code = models.CharField(max_length=10, blank=True, default="", verbose_name="เลขหัวข้อย่อย เช่น 1.1")
    sub_lessons_count = models.PositiveIntegerField(default=1, verbose_name="จำนวนบทเรียนย่อย")
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name="ระยะเวลาเรียน (นาที)")
    order = models.PositiveIntegerField(default=1, verbose_name="ลำดับการแสดงผล")
    # 📌 น้ำหนักคะแนนสำหรับคำนวณคะแนนรวมถ่วงน้ำหนักในแดชบอร์ด (เหมือนหน่วยกิตที่แต่ละวิชาไม่เท่ากัน)
    credit_weight = models.FloatField(default=1.0, verbose_name="น้ำหนักคะแนน (เหมือนหน่วยกิต)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['grade', 'chapter', 'subtopic_code', 'order']

    def __str__(self):
        return f"[{self.get_grade_display()}] {self.title}"


# 📌 4. ระบบแบบฝึกหัด / ข้อสอบ / เก็บคะแนน
class Question(models.Model):
    QUESTION_TYPES = (
        ('mcq', 'ปรนัย (เลือกคำตอบ)'),
        ('text', 'อัตนัย (พิมพ์คำตอบ)'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions', verbose_name="บทเรียนที่เกี่ยวข้อง")
    order = models.PositiveIntegerField(default=1, verbose_name="ลำดับข้อ")
    question_type = models.CharField(max_length=4, choices=QUESTION_TYPES, default='mcq', verbose_name="ประเภทคำถาม")
    text = models.TextField(verbose_name="โจทย์คำถาม")
    explanation = models.TextField(blank=True, default="", verbose_name="คำอธิบาย/เฉลย")
    points = models.PositiveIntegerField(default=1, verbose_name="คะแนนเต็มของข้อนี้")
    # สำหรับคำถามแบบอัตนัย: รายการคำตอบที่ยอมรับ (เทียบแบบไม่สนตัวพิมพ์เล็ก-ใหญ่ และช่องว่างส่วนเกิน)
    accepted_answers = models.JSONField(default=list, blank=True, verbose_name="คำตอบที่ยอมรับ (อัตนัย)")

    class Meta:
        ordering = ['lesson', 'order']

    def __str__(self):
        return f"[{self.lesson}] ข้อ {self.order}: {self.text[:40]}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices', verbose_name="คำถาม")
    order = models.PositiveIntegerField(default=1, verbose_name="ลำดับตัวเลือก")
    text = models.CharField(max_length=500, verbose_name="ข้อความตัวเลือก")
    is_correct = models.BooleanField(default=False, verbose_name="เป็นคำตอบที่ถูกต้อง")

    class Meta:
        ordering = ['question', 'order']

    def __str__(self):
        return self.text[:60]


class Attempt(models.Model):
    MODE_CHOICES = (
        ('practice', 'แบบฝึกหัด'),
        ('exam', 'ข้อสอบ'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attempts', verbose_name="ผู้ทำ")
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='practice', verbose_name="ประเภทการทำ")
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='attempts', verbose_name="บทเรียน (สำหรับแบบฝึกหัด)")
    grade = models.CharField(max_length=2, blank=True, default="", verbose_name="ระดับชั้น (สำหรับข้อสอบ)")
    chapter = models.PositiveIntegerField(null=True, blank=True, verbose_name="บทที่ (สำหรับข้อสอบ)")
    score = models.FloatField(default=0, verbose_name="คะแนนที่ได้")
    max_score = models.FloatField(default=0, verbose_name="คะแนนเต็ม")
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="เวลาที่ส่งคำตอบ")

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user} - {self.get_mode_display()} ({self.score}/{self.max_score})"

    @property
    def percent(self):
        if not self.max_score:
            return 0
        return round(self.score / self.max_score * 100, 1)


class Checkpoint(models.Model):
    """แบบทดสอบสั้นๆ ที่แทรกอยู่ระหว่างเนื้อหาบทเรียน ไม่เก็บคะแนน แค่บอกถูก/ผิดทันทีเพื่อให้อ่านไปทำไป"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='checkpoints', verbose_name="บทเรียนที่เกี่ยวข้อง")
    after_paragraph = models.PositiveIntegerField(default=1, verbose_name="แทรกหลังย่อหน้าที่ (นับจาก 1)")
    order = models.PositiveIntegerField(default=1, verbose_name="ลำดับ (ถ้ามีหลายข้อในตำแหน่งเดียวกัน)")
    text = models.TextField(verbose_name="คำถามสั้นๆ ระหว่างอ่าน")
    explanation = models.TextField(blank=True, default="", verbose_name="คำอธิบายเพิ่มเติม")

    class Meta:
        ordering = ['lesson', 'after_paragraph', 'order']

    def __str__(self):
        return f"[{self.lesson}] หลังย่อหน้า {self.after_paragraph}: {self.text[:40]}"


class CheckpointChoice(models.Model):
    checkpoint = models.ForeignKey(Checkpoint, on_delete=models.CASCADE, related_name='choices', verbose_name="คำถามระหว่างอ่าน")
    order = models.PositiveIntegerField(default=1)
    text = models.CharField(max_length=300, verbose_name="ข้อความตัวเลือก")
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['checkpoint', 'order']

    def __str__(self):
        return self.text[:60]


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers', verbose_name="การทำแบบฝึกหัด/ข้อสอบ")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='attempt_answers', verbose_name="คำถาม")
    order = models.PositiveIntegerField(default=1, verbose_name="ลำดับที่แสดงในการทำครั้งนี้")
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ตัวเลือกที่เลือก")
    text_answer = models.TextField(blank=True, default="", verbose_name="คำตอบที่พิมพ์")
    is_correct = models.BooleanField(default=False, verbose_name="ตอบถูกหรือไม่")
    points_earned = models.FloatField(default=0, verbose_name="คะแนนที่ได้ในข้อนี้")

    class Meta:
        ordering = ['attempt', 'order']

    def __str__(self):
        return f"Attempt#{self.attempt_id} - Q{self.question_id}"


# 📌 5. ประวัติการเข้าชม (สำหรับแท็บ "เข้าชมล่าสุด" ในหน้าโปรไฟล์)
# 📌 บันทึกเป็นแถวใหม่ทุกครั้งที่เข้าชม (ไม่ unique ต่อ user+รายการ) เพื่อเก็บประวัติการเข้าชมซ้ำไว้ทั้งหมด
# 📌 รองรับหลายประเภทกิจกรรม: เปิดบทเรียน / เปิดสื่อ 3D / เล่นการ์ดคำศัพท์จากคลังกลาง / เล่นการ์ดของฉัน
class LessonView(models.Model):
    ACTIVITY_CHOICES = (
        ('lesson', 'เปิดบทเรียน'),
        ('lesson_3d', 'เปิดสื่อ 3D Interactive'),
        ('flashcard_bank', 'เล่นการ์ดคำศัพท์ (คลังกลาง)'),
        ('flashcard_deck', 'เปิดชุดการ์ดของฉัน'),
        ('classroom_video', 'ดูคลิปวิดีโอห้องเรียน'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_views', verbose_name="ผู้ใช้งาน")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='lesson', verbose_name="ประเภทกิจกรรม")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='views', null=True, blank=True, verbose_name="บทเรียนที่เข้าชม")
    flashcard_deck = models.ForeignKey('FlashcardDeck', on_delete=models.SET_NULL, related_name='views', null=True, blank=True, verbose_name="ชุดการ์ดที่เข้าชม")
    classroom_video = models.ForeignKey('ClassroomVideo', on_delete=models.SET_NULL, related_name='views', null=True, blank=True, verbose_name="วิดีโอห้องเรียนที่เข้าชม")
    label = models.CharField(max_length=200, blank=True, default="", verbose_name="รายละเอียดเพิ่มเติม (เช่น ตัวกรองที่ใช้ หรือชื่อชุดการ์ดสำรอง)")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="เข้าชมเมื่อ")

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user} - {self.get_activity_type_display()} เมื่อ {self.viewed_at}"


# 📌 6. เครื่องมือจัดการห้องเรียนสำหรับคุณครู (คลิปวิดีโอ / ไฟล์เอกสาร / แบบทดสอบที่สร้างเอง)
class ClassroomVideo(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='videos', verbose_name="ห้องเรียน")
    title = models.CharField(max_length=200, verbose_name="ชื่อคลิป")
    youtube_url = models.URLField(blank=True, default="", verbose_name="ลิงก์ YouTube")
    video_file = models.FileField(upload_to='classroom_videos/%Y/%m/', blank=True, null=True, verbose_name="ไฟล์วิดีโอ")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ผู้เพิ่ม")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.classroom}] {self.title}"

    @property
    def youtube_embed_url(self):
        """แปลงลิงก์ YouTube หลายรูปแบบ (watch?v=, youtu.be/, embed/) ให้เป็นลิงก์ embed"""
        import re as _re
        if not self.youtube_url:
            return ""
        m = _re.search(r'(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{6,})', self.youtube_url)
        return f"https://www.youtube.com/embed/{m.group(1)}" if m else ""


class ClassroomFile(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='files', verbose_name="ห้องเรียน")
    title = models.CharField(max_length=200, verbose_name="ชื่อเอกสาร")
    file = models.FileField(upload_to='classroom_files/%Y/%m/', verbose_name="ไฟล์เอกสาร")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ผู้อัปโหลด")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"[{self.classroom}] {self.title}"

    @property
    def filename(self):
        return self.file.name.rsplit('/', 1)[-1]


class ClassroomQuiz(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='quizzes', verbose_name="ห้องเรียน")
    title = models.CharField(max_length=200, verbose_name="ชื่อแบบทดสอบ")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ผู้สร้าง")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Classroom quizzes"

    def __str__(self):
        return f"[{self.classroom}] {self.title}"

    @property
    def question_count(self):
        return self.questions.count()


class ClassroomQuizQuestion(models.Model):
    QUESTION_TYPES = (
        ('mcq', 'ปรนัย (เลือกคำตอบ)'),
        ('text', 'อัตนัย (พิมพ์คำตอบ)'),
    )
    quiz = models.ForeignKey(ClassroomQuiz, on_delete=models.CASCADE, related_name='questions', verbose_name="แบบทดสอบ")
    order = models.PositiveIntegerField(default=1, verbose_name="ลำดับข้อ")
    question_type = models.CharField(max_length=4, choices=QUESTION_TYPES, default='mcq', verbose_name="ประเภทคำถาม")
    text = models.TextField(verbose_name="โจทย์คำถาม")
    points = models.PositiveIntegerField(default=1, verbose_name="คะแนนเต็มของข้อนี้")
    accepted_answers = models.JSONField(default=list, blank=True, verbose_name="คำตอบที่ยอมรับ (อัตนัย)")

    class Meta:
        ordering = ['quiz', 'order']

    def __str__(self):
        return f"[{self.quiz}] ข้อ {self.order}"


class ClassroomQuizChoice(models.Model):
    question = models.ForeignKey(ClassroomQuizQuestion, on_delete=models.CASCADE, related_name='choices', verbose_name="คำถาม")
    order = models.PositiveIntegerField(default=1)
    text = models.CharField(max_length=500, verbose_name="ข้อความตัวเลือก")
    is_correct = models.BooleanField(default=False, verbose_name="เป็นคำตอบที่ถูกต้อง")

    class Meta:
        ordering = ['question', 'order']

    def __str__(self):
        return self.text[:60]


class ClassroomQuizAttempt(models.Model):
    quiz = models.ForeignKey(ClassroomQuiz, on_delete=models.CASCADE, related_name='attempts', verbose_name="แบบทดสอบ")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='classroom_quiz_attempts', verbose_name="ผู้ทำ")
    # 📌 ข้อมูลที่นักเรียนกรอกเองก่อนเริ่มทำ ใช้แยกตัวตนผู้ทำให้ชัดเจน (เผื่อบัญชีเดียวใช้กันหลายคน หรือครูต้องการเทียบกับรายชื่อจริง)
    student_name = models.CharField(max_length=200, blank=True, default="", verbose_name="ชื่อ-นามสกุล")
    student_class = models.CharField(max_length=50, blank=True, default="", verbose_name="ชั้น")
    student_number = models.CharField(max_length=10, blank=True, default="", verbose_name="เลขที่")
    score = models.FloatField(default=0, verbose_name="คะแนนที่ได้")
    max_score = models.FloatField(default=0, verbose_name="คะแนนเต็ม")
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="เวลาที่ส่งคำตอบ")

    class Meta:
        ordering = ['-started_at']
        # 📌 ทำได้คนละครั้งเดียวต่อแบบทดสอบหนึ่งชุด (กันการเข้ามาทำซ้ำ)
        unique_together = ('quiz', 'user')

    def __str__(self):
        return f"{self.user} - {self.quiz} ({self.score}/{self.max_score})"

    @property
    def percent(self):
        if not self.max_score:
            return 0
        return round(self.score / self.max_score * 100, 1)


class ClassroomQuizAnswer(models.Model):
    attempt = models.ForeignKey(ClassroomQuizAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name="การทำแบบทดสอบ")
    question = models.ForeignKey(ClassroomQuizQuestion, on_delete=models.CASCADE, related_name='attempt_answers', verbose_name="คำถาม")
    order = models.PositiveIntegerField(default=1, verbose_name="ลำดับที่แสดงในการทำครั้งนี้")
    selected_choice = models.ForeignKey(ClassroomQuizChoice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ตัวเลือกที่เลือก")
    text_answer = models.TextField(blank=True, default="", verbose_name="คำตอบที่พิมพ์")
    is_correct = models.BooleanField(default=False, verbose_name="ตอบถูกหรือไม่")
    points_earned = models.FloatField(default=0, verbose_name="คะแนนที่ได้ในข้อนี้")

    class Meta:
        ordering = ['attempt', 'order']

    def __str__(self):
        return f"Attempt#{self.attempt_id} - Q{self.question_id}"


# 📌 การ์ดคำศัพท์ที่นักเรียนสร้างเอง (ส่วนตัวเฉพาะคนสร้าง ไม่แชร์ให้คนอื่นเห็น)
class FlashcardDeck(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flashcard_decks', verbose_name="เจ้าของ")
    title = models.CharField(max_length=200, verbose_name="ชื่อชุดการ์ด")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.owner})"

    @property
    def card_count(self):
        return self.cards.count()


class Flashcard(models.Model):
    deck = models.ForeignKey(FlashcardDeck, on_delete=models.CASCADE, related_name='cards', verbose_name="ชุดการ์ด")
    front = models.TextField(verbose_name="คำถาม/คำศัพท์ (ด้านหน้า)")
    back = models.TextField(verbose_name="คำตอบ/ความหมาย (ด้านหลัง)")
    order = models.PositiveIntegerField(default=1, verbose_name="ลำดับ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['deck', 'order', 'created_at']

    def __str__(self):
        return self.front[:60]


# 📌 7. Feedback จากผู้ใช้ต่อคำตอบของฟีเจอร์ "ถาม AI" (👍/👎) ใช้ดูว่าคำตอบช่วยได้จริงไหม เพื่อปรับปรุงต่อ
class AIFeedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_feedback', verbose_name="ผู้ใช้งาน")
    question = models.TextField(verbose_name="คำถาม")
    answer = models.TextField(verbose_name="คำตอบของ AI")
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_feedback', verbose_name="บทเรียนที่เกี่ยวข้อง (ถ้ามี)")
    is_helpful = models.BooleanField(verbose_name="เป็นประโยชน์หรือไม่ (True=👍, False=👎)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="ให้ feedback เมื่อ")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        mark = "👍" if self.is_helpful else "👎"
        return f"{self.user} {mark} เมื่อ {self.created_at}"


# 📌 8. คลังเอกสารอ้างอิง (PDF) ที่แอดมินอัปโหลดผ่านหน้า Admin ให้ฟีเจอร์ "ถาม AI" ค้นหาเนื้อหาไปแนบตอบด้วย (RAG)
# ไม่ผูกกับบทเรียนใดบทเรียนหนึ่งโดยเฉพาะ ถือเป็นคลังกลางที่ใช้ประกอบการตอบทุกคำถาม
class KnowledgeDocument(models.Model):
    title = models.CharField(max_length=200, verbose_name="ชื่อเอกสาร")
    file = models.FileField(upload_to='knowledge_docs/%Y/%m/', verbose_name="ไฟล์ PDF")
    extracted_text = models.TextField(blank=True, default="", verbose_name="เนื้อหาที่แกะจากไฟล์ (ระบบสร้างให้อัตโนมัติตอนอัปโหลด)")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='knowledge_documents', verbose_name="ผู้อัปโหลด")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="อัปโหลดเมื่อ")

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title