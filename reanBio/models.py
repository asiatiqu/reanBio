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