import os
import random
import re
from itertools import groupby

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.html import escape

from .models import UserProfile, Classroom, Lesson, Question, Choice, Attempt, AttemptAnswer
from .forms import UserSignUpForm


# 📌 ช่วยเน้นคำค้นหาในเนื้อหา และตัดข้อความให้เหลือแค่ช่วงที่เจอคำ (snippet)
def _highlight(text, query):
    escaped_text = escape(text)
    if not query:
        return escaped_text
    pattern = re.compile(re.escape(escape(query)), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark class='bg-yellow-200 rounded px-0.5'>{m.group(0)}</mark>", escaped_text)


def _render_content_html(text, query):
    """แปลงเนื้อหาบทเรียนเป็น HTML: escape ป้องกัน XSS, เน้นคำค้นหา, และขึ้นย่อหน้าใหม่ตามบรรทัดว่าง"""
    highlighted = _highlight(text or "", query)
    paragraphs = [p.strip().replace("\n", "<br>") for p in highlighted.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>" for p in paragraphs)


def _build_content_snippet(content, query, radius=70):
    if not content or not query:
        return ""
    lower_content = content.lower()
    lower_query = query.lower()
    idx = lower_content.find(lower_query)
    if idx == -1:
        return ""
    start = max(0, idx - radius)
    end = min(len(content), idx + len(query) + radius)
    snippet = content[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(content):
        snippet = snippet + "…"
    return _highlight(snippet, query)

# 📌 Decorator เช็กสิทธิ์เฉพาะคุณครู
def teacher_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if getattr(request.user, 'is_teacher', False):
            return view_func(request, *args, **kwargs)
        return redirect('my_classrooms')
    return _wrapped_view

def home(request):
    return render(request, 'index.html')

def signup(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data.get('role')
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.save()

            user_grade = request.POST.get('grade_level', request.POST.get('grade', '')).strip()
            UserProfile.objects.create(
                user=user,
                grade=user_grade
            )

            login(request, user)
            if getattr(user, 'is_teacher', False):
                return redirect('teacher_dashboard')
            return redirect('home')
    else:
        form = UserSignUpForm()

    return render(request, 'reanBio/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # 🛑 บล็อกบัญชี Admin ไม่ให้ล็อกอินผ่านหน้าเว็บปกติ
            if user.is_superuser or user.is_staff:
                form.add_error(None, 'บัญชีผู้ดูแลระบบ (Admin) ไม่สามารถเข้าใช้งานหน้านี้ได้ กรุณาเข้าสู่ระบบผ่านหน้า /admin/')
            else:
                login(request, user)
                if getattr(user, 'is_teacher', False):
                    return redirect('teacher_dashboard')
                return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'reanBio/login.html', {'form': form})

def lessons_view(request):
    grade_filter = request.GET.get('grade', 'all')
    search_query = request.GET.get('q', '').strip()

    lessons = Lesson.objects.all()

    if grade_filter in ['m4', 'm5', 'm6']:
        lessons = lessons.filter(grade=grade_filter)

    # 📌 ค้นหาทั้งชื่อบทเรียน คำอธิบายย่อย และเนื้อหาแบบเต็ม
    if search_query:
        lessons = lessons.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(content__icontains=search_query)
        )

    lessons = list(lessons)

    # 📌 ถ้ามีคำค้นหา แนบตัวอย่างข้อความ (snippet) ที่เจอคำในเนื้อหา พร้อมไฮไลต์คำนั้น
    if search_query:
        for lesson in lessons:
            if search_query.lower() in lesson.title.lower():
                lesson.search_snippet = ""
            else:
                lesson.search_snippet = _build_content_snippet(lesson.content, search_query) or \
                    _build_content_snippet(lesson.description, search_query)
    else:
        for lesson in lessons:
            lesson.search_snippet = ""

    # 📌 จัดกลุ่มบทเรียนตาม "บทที่" ของหนังสือเรียน (lessons ถูกเรียงตาม grade, chapter, subtopic_code อยู่แล้วจาก Meta.ordering)
    chapter_groups = []
    for (grade, chapter, chapter_title), group_iter in groupby(lessons, key=lambda l: (l.grade, l.chapter, l.chapter_title)):
        chapter_groups.append({
            'grade': grade,
            'chapter': chapter,
            'chapter_title': chapter_title,
            'lessons': list(group_iter),
        })

    return render(request, 'reanBio/lessons.html', {
        'lessons': lessons,
        'chapter_groups': chapter_groups,
        'current_grade': grade_filter,
        'search_query': search_query,
    })

@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    return render(request, 'reanBio/profile.html', {'profile': user_profile})

def user_logout(request):
    logout(request)
    return redirect('home')

# 📌 แดชบอร์ดจัดการห้องเรียนของคุณครู
@teacher_required
def teacher_dashboard_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Classroom.objects.create(name=name, teacher=request.user)
            messages.success(request, 'สร้างห้องเรียนสำเร็จ!')
            return redirect('teacher_dashboard')

    classrooms = Classroom.objects.filter(teacher=request.user).order_by('-created_at')
    return render(request, 'reanBio/teacher_dashboard.html', {'classrooms': classrooms})

# 📌 หน้าห้องเรียนของฉัน (สำหรับนักเรียน)
@login_required
def my_classroom_view(request):
    joined_classrooms = request.user.joined_classrooms.all().order_by('-created_at')
    return render(request, 'reanBio/my_classrooms.html', {'classrooms': joined_classrooms})

# 📌 ฟังก์ชันให้นักเรียนกรอกรหัสเข้าร่วมห้องเรียน
@login_required
def join_classroom_view(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        try:
            classroom = Classroom.objects.get(code=code)
            classroom.students.add(request.user)
            messages.success(request, f'เข้าร่วมห้องเรียน "{classroom.name}" เรียบร้อยแล้ว!')
            return redirect('classroom_detail', code=classroom.code)
        except Classroom.DoesNotExist:
            messages.error(request, 'ไม่พบห้องเรียนรหัสนี้ กรุณาตรวจสอบรหัสอีกครั้ง')
            return redirect('my_classrooms')
    return redirect('my_classrooms')

# 📌 รายละเอียดภายในห้องเรียน
@login_required
def classroom_detail_view(request, code):
    classroom = get_object_or_404(Classroom, code=code)
    return render(request, 'reanBio/classroom_detail.html', {'classroom': classroom})

@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    # แยกการดึงข้อมูลห้องเรียนตามบทบาทผู้ใช้
    if getattr(request.user, 'is_teacher', False):
        classrooms = Classroom.objects.filter(teacher=request.user).order_by('-created_at')
    else:
        classrooms = request.user.joined_classrooms.all().order_by('-created_at')

    return render(request, 'reanBio/profile.html', {
        'profile': user_profile,
        'classrooms': classrooms
    })

@login_required
def my_classroom_view(request):
    # 🛑 ถ้าเป็นคุณครู ให้เด้งไปหน้าแดชบอร์ดสร้าง/จัดการห้องเรียนทันที
    if getattr(request.user, 'is_teacher', False):
        return redirect('teacher_dashboard')

    joined_classrooms = request.user.joined_classrooms.all().order_by('-created_at')
    return render(request, 'reanBio/my_classrooms.html', {'classrooms': joined_classrooms})

def lesson_detail_view(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    search_query = request.GET.get('q', '').strip()
    content_html = _render_content_html(lesson.content, search_query)

    return render(request, 'reanBio/lesson_detail.html', {
        'lesson': lesson,
        'content_html': content_html,
        'search_query': search_query,
    })


# ============================================================
# 📌 5. ระบบแบบฝึกหัด / ข้อสอบ / เก็บคะแนน
# ============================================================

def _grade_text_answer(question, raw_answer):
    """ตรวจคำตอบแบบอัตนัยแบบผ่อนปรน: เทียบคำสำคัญแบบไม่สนตัวพิมพ์เล็ก-ใหญ่และช่องว่างส่วนเกิน"""
    normalized = " ".join((raw_answer or "").strip().lower().split())
    if not normalized:
        return False
    for accepted in (question.accepted_answers or []):
        acc_norm = " ".join(str(accepted).strip().lower().split())
        if acc_norm and (acc_norm in normalized or normalized in acc_norm):
            return True
    return False


@login_required
def lesson_exercise_view(request, pk):
    """หน้าภาพรวมแบบฝึกหัดของบทเรียนหนึ่งๆ พร้อมประวัติการทำของผู้ใช้"""
    lesson = get_object_or_404(Lesson, pk=pk)
    questions = list(lesson.questions.all())
    history = Attempt.objects.filter(
        user=request.user, lesson=lesson, mode='practice', submitted_at__isnull=False
    ).order_by('-submitted_at')

    return render(request, 'reanBio/lesson_exercise.html', {
        'lesson': lesson,
        'question_count': len(questions),
        'history': history,
    })


@login_required
def start_practice_attempt(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    questions = list(lesson.questions.all())
    if not questions:
        messages.info(request, "บทเรียนนี้ยังไม่มีแบบฝึกหัด")
        return redirect('lesson_detail', pk=lesson.pk)

    attempt = Attempt.objects.create(
        user=request.user, mode='practice', lesson=lesson,
        max_score=sum(q.points for q in questions),
    )
    for i, q in enumerate(questions, start=1):
        AttemptAnswer.objects.create(attempt=attempt, question=q, order=i)

    return redirect('attempt_take', attempt_pk=attempt.pk)


@login_required
def exam_start_view(request):
    if request.method == 'POST':
        grade = request.POST.get('grade', 'm4')
        chapter = request.POST.get('chapter', '').strip()
        try:
            num_questions = int(request.POST.get('num_questions', 10))
        except ValueError:
            num_questions = 10

        pool = Question.objects.filter(lesson__grade=grade)
        if chapter:
            pool = pool.filter(lesson__chapter=chapter)
        pool = list(pool)

        if not pool:
            messages.error(request, "ไม่พบคำถามสำหรับตัวเลือกที่เลือก กรุณาลองใหม่")
            return redirect('exam_start')

        num_questions = max(1, min(num_questions, len(pool)))
        selected = random.sample(pool, num_questions)

        attempt = Attempt.objects.create(
            user=request.user, mode='exam', grade=grade,
            chapter=int(chapter) if chapter else None,
            max_score=sum(q.points for q in selected),
        )
        for i, q in enumerate(selected, start=1):
            AttemptAnswer.objects.create(attempt=attempt, question=q, order=i)

        return redirect('attempt_take', attempt_pk=attempt.pk)

    chapters = list(
        Lesson.objects.filter(grade='m4', chapter__isnull=False)
        .exclude(chapter_title="")
        .values_list('chapter', 'chapter_title')
        .distinct()
        .order_by('chapter')
    )
    total_questions = Question.objects.filter(lesson__grade='m4').count()

    return render(request, 'reanBio/exam_start.html', {
        'chapters': chapters,
        'total_questions': total_questions,
    })


@login_required
def attempt_take_view(request, attempt_pk):
    attempt = get_object_or_404(Attempt, pk=attempt_pk, user=request.user)
    if attempt.submitted_at:
        return redirect('attempt_result', attempt_pk=attempt.pk)

    answers = list(
        attempt.answers.select_related('question')
        .prefetch_related('question__choices')
        .order_by('order')
    )

    if request.method == 'POST':
        total_score = 0
        for ans in answers:
            q = ans.question
            if q.question_type == 'mcq':
                choice_id = request.POST.get(f'q{ans.id}')
                selected = q.choices.filter(pk=choice_id).first() if choice_id else None
                is_correct = bool(selected and selected.is_correct)
                ans.selected_choice = selected
                ans.is_correct = is_correct
                ans.points_earned = q.points if is_correct else 0
            else:
                text_val = request.POST.get(f'q{ans.id}', '').strip()
                is_correct = _grade_text_answer(q, text_val)
                ans.text_answer = text_val
                ans.is_correct = is_correct
                ans.points_earned = q.points if is_correct else 0
            ans.save()
            total_score += ans.points_earned

        attempt.score = total_score
        attempt.submitted_at = timezone.now()
        attempt.save()
        return redirect('attempt_result', attempt_pk=attempt.pk)

    return render(request, 'reanBio/attempt_take.html', {'attempt': attempt, 'answers': answers})


@login_required
def attempt_result_view(request, attempt_pk):
    attempt = get_object_or_404(Attempt, pk=attempt_pk, user=request.user)
    answers = (
        attempt.answers.select_related('question', 'selected_choice')
        .prefetch_related('question__choices')
        .order_by('order')
    )
    return render(request, 'reanBio/attempt_result.html', {'attempt': attempt, 'answers': answers})


@login_required
def dashboard_view(request):
    attempts = list(
        Attempt.objects.filter(user=request.user, submitted_at__isnull=False)
        .select_related('lesson')
        .order_by('submitted_at')
    )
    practice_attempts = [a for a in attempts if a.mode == 'practice']
    exam_attempts = [a for a in attempts if a.mode == 'exam']

    def label_for(a):
        if a.lesson:
            return str(a.lesson.title)
        if a.chapter:
            return f"ข้อสอบบทที่ {a.chapter}"
        return "ข้อสอบรวม"

    def series(qs):
        return [
            {
                'date': a.submitted_at.strftime('%d/%m/%y %H:%M'),
                'percent': a.percent,
                'label': label_for(a),
            }
            for a in qs
        ]

    def trend(qs):
        if len(qs) < 2:
            return None
        mid = max(1, len(qs) // 2)
        first_half = qs[:mid]
        second_half = qs[mid:] or qs[-1:]
        avg1 = sum(a.percent for a in first_half) / len(first_half)
        avg2 = sum(a.percent for a in second_half) / len(second_half)
        return round(avg2 - avg1, 1)

    return render(request, 'reanBio/dashboard.html', {
        'practice_attempts': list(reversed(practice_attempts)),
        'exam_attempts': list(reversed(exam_attempts)),
        'practice_series': series(practice_attempts),
        'exam_series': series(exam_attempts),
        'practice_trend': trend(practice_attempts),
        'exam_trend': trend(exam_attempts),
        'total_attempts': len(attempts),
    })


@login_required
def exercise_pdf_view(request, pk):
    """สร้างไฟล์ PDF ของแบบฝึกหัดในบทเรียนนี้ (ไม่เฉลย) สำหรับพิมพ์ไปทำบนกระดาษ"""
    lesson = get_object_or_404(Lesson, pk=pk)
    questions = list(lesson.questions.prefetch_related('choices').all())
    if not questions:
        raise Http404("บทเรียนนี้ยังไม่มีแบบฝึกหัด")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    font_dir = os.path.join(os.path.dirname(__file__), 'static', 'reanBio', 'fonts')
    if 'Waree' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('Waree', os.path.join(font_dir, 'Waree.ttf')))
        pdfmetrics.registerFont(TTFont('Waree-Bold', os.path.join(font_dir, 'Waree-Bold.ttf')))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="exercise_{lesson.pk}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    bottom_limit = 2.2 * cm
    y = height - margin

    def wrap_text(text, font, size, max_width):
        lines = []
        current = ""
        for ch in text:
            test = current + ch
            if pdfmetrics.stringWidth(test, font, size) > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        return lines or [""]

    def draw_wrapped(text, x, start_y, font, size, max_width, leading):
        cur_y = start_y
        for line in wrap_text(text, font, size, max_width):
            if cur_y < bottom_limit:
                p.showPage()
                cur_y = height - margin
            p.setFont(font, size)
            p.drawString(x, cur_y, line)
            cur_y -= leading
        return cur_y

    p.setFont('Waree-Bold', 16)
    p.drawCentredString(width / 2, y, f"แบบฝึกหัด: {lesson.title}")
    y -= 0.9 * cm
    p.setFont('Waree', 10)
    p.drawString(margin, y, "ชื่อ-นามสกุล: ..........................................  เลขที่: ..........  วันที่: ..........")
    y -= 1.0 * cm

    content_width = width - 2 * margin
    for idx, q in enumerate(questions, start=1):
        if y < bottom_limit + 1.5 * cm:
            p.showPage()
            y = height - margin
        y = draw_wrapped(f"{idx}. {q.text}", margin, y, 'Waree-Bold', 11, content_width, 0.55 * cm)
        y -= 0.15 * cm

        if q.question_type == 'mcq':
            letters = "กขคงจฉชซ"
            for c_idx, choice in enumerate(q.choices.all()):
                letter = letters[c_idx] if c_idx < len(letters) else str(c_idx + 1)
                y = draw_wrapped(f"   {letter}. {choice.text}", margin, y, 'Waree', 10, content_width, 0.5 * cm)
        else:
            p.setFont('Waree', 10)
            for _ in range(3):
                if y < bottom_limit:
                    p.showPage()
                    y = height - margin
                p.line(margin, y, width - margin, y)
                y -= 0.85 * cm

        y -= 0.35 * cm

    p.save()
    return response