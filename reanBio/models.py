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

    def __str__(self):
        return f"Profile of {self.user.username}"


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