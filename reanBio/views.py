import os
import csv
import json
import random
import re
from itertools import groupby

from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.html import escape

from .models import (
    UserProfile, Classroom, Lesson, Question, Choice, Attempt, AttemptAnswer, Checkpoint, LessonView,
    ClassroomVideo, ClassroomFile, ClassroomQuiz, ClassroomQuizQuestion, ClassroomQuizChoice,
    ClassroomQuizAttempt, ClassroomQuizAnswer,
)
from .forms import UserSignUpForm


# 📌 ช่วยเน้นคำค้นหาในเนื้อหา และตัดข้อความให้เหลือแค่ช่วงที่เจอคำ (snippet)
def _highlight(text, query):
    escaped_text = escape(text)
    if not query:
        return escaped_text
    pattern = re.compile(re.escape(escape(query)), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark class='bg-yellow-200 rounded px-0.5'>{m.group(0)}</mark>", escaped_text)


def _render_checkpoint_html(checkpoint):
    """สร้าง HTML การ์ดคำถามสั้นๆ ระหว่างเนื้อหา ตรวจถูก/ผิดด้วย JS ฝั่งเบราว์เซอร์ทันที ไม่เก็บคะแนนลงฐานข้อมูล"""
    choices_html = "".join(
        f'''<label class="flex items-center gap-3 p-2.5 rounded-xl border border-slate-100 hover:bg-white cursor-pointer transition">
                <input type="radio" name="cp{checkpoint.pk}" value="{c.pk}" data-correct="{"1" if c.is_correct else "0"}" class="accent-bio-main w-4 h-4">
                <span class="text-sm text-slate-700">{escape(c.text)}</span>
            </label>'''
        for c in checkpoint.choices.all()
    )
    explanation_html = f'<p class="text-xs text-slate-500 mt-2">{escape(checkpoint.explanation)}</p>' if checkpoint.explanation else ""
    return f'''
    <div class="checkpoint-quiz not-prose my-4 p-5 bg-bio-light/50 border-2 border-dashed border-bio-main/30 rounded-2xl" data-cp-id="{checkpoint.pk}">
        <p class="font-bold text-bio-dark text-sm mb-3">ลองตรวจสอบความเข้าใจ: {escape(checkpoint.text)}</p>
        <div class="space-y-1.5">{choices_html}</div>
        <button type="button" onclick="checkCheckpoint({checkpoint.pk})"
            class="mt-3 px-5 py-2 bg-bio-main hover:bg-bio-dark text-white text-xs font-bold rounded-full transition">
            ตรวจคำตอบ
        </button>
        <div id="cp-result-{checkpoint.pk}" class="mt-2 text-sm font-bold hidden"></div>
        <div id="cp-explain-{checkpoint.pk}" class="hidden">{explanation_html}</div>
    </div>'''


def _render_content_html(text, query, checkpoints=None):
    """แปลงเนื้อหาบทเรียนเป็น HTML: escape ป้องกัน XSS, เน้นคำค้นหา, ขึ้นย่อหน้าใหม่ตามบรรทัดว่าง
    และแทรกคำถามสั้นๆ (checkpoint) ระหว่างย่อหน้าตามตำแหน่งที่กำหนดไว้"""
    highlighted = _highlight(text or "", query)
    paragraphs = [p.strip().replace("\n", "<br>") for p in highlighted.split("\n\n") if p.strip()]

    checkpoints_by_para = {}
    for cp in (checkpoints or []):
        checkpoints_by_para.setdefault(cp.after_paragraph, []).append(cp)

    html_parts = []
    for idx, para in enumerate(paragraphs, start=1):
        html_parts.append(f"<p>{para}</p>")
        for cp in checkpoints_by_para.get(idx, []):
            html_parts.append(_render_checkpoint_html(cp))
    return "".join(html_parts)


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


def _chapters_by_grade():
    """คืนค่า dict {grade: [เลขบทที่ทั้งหมดของ grade นั้น]} ใช้ในฟอร์มกรอง/สร้างแบบทดสอบ"""
    mapping = {}
    for grade, chapter in Lesson.objects.values_list('grade', 'chapter').distinct().order_by('grade', 'chapter'):
        mapping.setdefault(grade, []).append(chapter)
    return mapping


# ============================================================
# 📌 การ์ดคำศัพท์แบบพลิกดู (Interactive Flashcards)
# ============================================================
def flashcards_view(request):
    """สุ่มการ์ดคำศัพท์จากคลังคำถามของบทเรียน ให้พลิกดูหน้า-หลังเพื่อทบทวนความรู้
    (ไม่เก็บคะแนน ไม่ต้องเข้าสู่ระบบ) กรองตามระดับชั้น/บทที่ได้"""
    grade_filter = request.GET.get('grade', 'all')
    chapter_filter = request.GET.get('chapter', '').strip()

    questions = Question.objects.select_related('lesson').prefetch_related('choices')
    if grade_filter in ['m4', 'm5', 'm6']:
        questions = questions.filter(lesson__grade=grade_filter)
    if chapter_filter.isdigit():
        questions = questions.filter(lesson__chapter=int(chapter_filter))

    questions = list(questions)
    random.shuffle(questions)
    questions = questions[:60]  # จำกัดจำนวนการ์ดต่อรอบไม่ให้เยอะเกินไป

    cards = []
    for q in questions:
        if q.question_type == 'mcq':
            back = next((c.text for c in q.choices.all() if c.is_correct), '')
        else:
            back = (q.accepted_answers or [''])[0]
        if q.explanation:
            back = f"{back}\n\n{q.explanation}" if back else q.explanation
        cards.append({
            'front': q.text,
            'back': back or 'ยังไม่มีเฉลยสำหรับข้อนี้',
            'lesson': f"{q.lesson.subtopic_code} {q.lesson.title}".strip(),
        })

    chapters_by_grade = _chapters_by_grade()
    if grade_filter in chapters_by_grade:
        available_chapters = chapters_by_grade[grade_filter]
    else:
        available_chapters = sorted({c for chapters in chapters_by_grade.values() for c in chapters})

    return render(request, 'reanBio/flashcards.html', {
        'cards_json': json.dumps(cards, ensure_ascii=False),
        'card_count': len(cards),
        'current_grade': grade_filter,
        'current_chapter': chapter_filter,
        'available_chapters': available_chapters,
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
    quizzes = list(classroom.quizzes.all())

    # 📌 ให้นักเรียนเห็นสถานะการทำแบบทดสอบของตัวเอง (ทำได้คนละครั้งเดียว)
    if not getattr(request.user, 'is_teacher', False):
        my_attempts = {
            a.quiz_id: a for a in
            ClassroomQuizAttempt.objects.filter(quiz__classroom=classroom, user=request.user)
        }
        for quiz in quizzes:
            quiz.my_attempt = my_attempts.get(quiz.id)

    return render(request, 'reanBio/classroom_detail.html', {
        'classroom': classroom,
        'videos': classroom.videos.all(),
        'quizzes': quizzes,
        'files': classroom.files.all(),
    })


# ============================================================
# 📌 6. เครื่องมือจัดการห้องเรียนสำหรับคุณครู (คลิปวิดีโอ / ไฟล์เอกสาร / แบบทดสอบที่สร้างเอง)
# ============================================================

def _can_manage_classroom(user, classroom):
    """สิทธิ์จัดการเครื่องมือของห้องเรียน: เป็นคุณครูเจ้าของห้อง หรือเป็นคุณครูคนอื่น (ตามสิทธิ์เดิมของหน้านี้)"""
    return user.is_authenticated and (user == classroom.teacher or getattr(user, 'is_teacher', False))


@login_required
def classroom_add_video_view(request, code):
    classroom = get_object_or_404(Classroom, code=code)
    if not _can_manage_classroom(request.user, classroom):
        return redirect('classroom_detail', code=code)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        youtube_url = request.POST.get('youtube_url', '').strip()
        video_file = request.FILES.get('video_file')
        if not title or not (youtube_url or video_file):
            messages.error(request, 'กรุณาใส่ชื่อคลิป และลิงก์ YouTube หรือไฟล์วิดีโออย่างน้อย 1 อย่าง')
            return redirect('classroom_add_video', code=code)

        ClassroomVideo.objects.create(
            classroom=classroom, title=title, youtube_url=youtube_url,
            video_file=video_file, added_by=request.user,
        )
        messages.success(request, 'เพิ่มคลิปวิดีโอเรียบร้อยแล้ว')
        return redirect('classroom_detail', code=code)

    return render(request, 'reanBio/classroom_add_video.html', {'classroom': classroom})


@login_required
def classroom_add_file_view(request, code):
    classroom = get_object_or_404(Classroom, code=code)
    if not _can_manage_classroom(request.user, classroom):
        return redirect('classroom_detail', code=code)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        uploaded_file = request.FILES.get('file')
        if not title or not uploaded_file:
            messages.error(request, 'กรุณาใส่ชื่อเอกสารและเลือกไฟล์')
            return redirect('classroom_add_file', code=code)
        if uploaded_file.size > 20 * 1024 * 1024:
            messages.error(request, 'ไฟล์มีขนาดใหญ่เกินไป (จำกัดไม่เกิน 20MB)')
            return redirect('classroom_add_file', code=code)

        ClassroomFile.objects.create(
            classroom=classroom, title=title, file=uploaded_file, added_by=request.user,
        )
        messages.success(request, 'อัปโหลดไฟล์การสอนเรียบร้อยแล้ว')
        return redirect('classroom_detail', code=code)

    return render(request, 'reanBio/classroom_add_file.html', {'classroom': classroom})


@login_required
def classroom_add_quiz_view(request, code):
    classroom = get_object_or_404(Classroom, code=code)
    if not _can_manage_classroom(request.user, classroom):
        return redirect('classroom_detail', code=code)

    if request.method == 'POST':
        title = request.POST.get('quiz_title', '').strip()
        indices_raw = request.POST.get('question_indices', '').strip()
        indices = [n for n in indices_raw.split(',') if n.strip() != '']

        if not title or not indices:
            messages.error(request, 'กรุณาใส่ชื่อแบบทดสอบและคำถามอย่างน้อย 1 ข้อ')
            return redirect('classroom_add_quiz', code=code)

        quiz = ClassroomQuiz.objects.create(classroom=classroom, title=title, created_by=request.user)

        order = 0
        for n in indices:
            q_text = request.POST.get(f'q_text_{n}', '').strip()
            if not q_text:
                continue
            order += 1
            q_type = request.POST.get(f'q_type_{n}', 'mcq')
            try:
                points = max(1, int(request.POST.get(f'q_points_{n}', 1)))
            except (ValueError, TypeError):
                points = 1

            if q_type == 'text':
                accepted_raw = request.POST.get(f'q_accepted_{n}', '').strip()
                accepted_answers = [a.strip() for a in accepted_raw.split(',') if a.strip()]
                ClassroomQuizQuestion.objects.create(
                    quiz=quiz, order=order, question_type='text', text=q_text,
                    points=points, accepted_answers=accepted_answers,
                )
            else:
                question = ClassroomQuizQuestion.objects.create(
                    quiz=quiz, order=order, question_type='mcq', text=q_text, points=points,
                )
                choice_texts = request.POST.getlist(f'q_choice_{n}')
                correct_idx_raw = request.POST.get(f'q_correct_{n}', '')
                added_choice = False
                for c_idx, c_text in enumerate(choice_texts):
                    c_text = c_text.strip()
                    if not c_text:
                        continue
                    ClassroomQuizChoice.objects.create(
                        question=question, order=c_idx + 1, text=c_text,
                        is_correct=(str(c_idx) == correct_idx_raw),
                    )
                    added_choice = True
                if not added_choice:
                    question.delete()
                    order -= 1

        if quiz.questions.count() == 0:
            quiz.delete()
            messages.error(request, 'กรุณากรอกคำถามให้ครบถ้วนอย่างน้อย 1 ข้อ (ข้อแบบเลือกคำตอบต้องมีตัวเลือกด้วย)')
            return redirect('classroom_add_quiz', code=code)

        messages.success(request, 'สร้างแบบทดสอบเรียบร้อยแล้ว')
        return redirect('classroom_detail', code=code)

    return render(request, 'reanBio/classroom_add_quiz.html', {'classroom': classroom})


@login_required
def classroom_quiz_start_view(request, quiz_pk):
    """หน้ากรอกข้อมูลผู้ทำ (ชื่อ-นามสกุล/ชั้น/เลขที่) ก่อนเริ่มทำแบบทดสอบ
    ทำได้คนละครั้งเดียวต่อแบบทดสอบหนึ่งชุด: ถ้าเคยเริ่มไว้แล้วให้กลับไปทำต่อ/ดูผลแทนการเริ่มใหม่"""
    quiz = get_object_or_404(ClassroomQuiz, pk=quiz_pk)
    if getattr(request.user, 'is_teacher', False):
        messages.info(request, "บทบาทคุณครูใช้สำหรับสร้างแบบทดสอบเท่านั้น ไม่มีการทำแบบทดสอบ")
        return redirect('classroom_detail', code=quiz.classroom.code)

    existing = ClassroomQuizAttempt.objects.filter(quiz=quiz, user=request.user).first()
    if existing:
        if existing.submitted_at:
            messages.info(request, "คุณทำแบบทดสอบนี้ไปแล้ว ทำได้เพียงครั้งเดียวเท่านั้น")
            return redirect('classroom_quiz_result', attempt_pk=existing.pk)
        return redirect('classroom_quiz_take', attempt_pk=existing.pk)

    questions = list(quiz.questions.prefetch_related('choices').all())
    if not questions:
        messages.error(request, 'แบบทดสอบนี้ยังไม่มีคำถาม')
        return redirect('classroom_detail', code=quiz.classroom.code)

    if request.method == 'POST':
        student_name = request.POST.get('student_name', '').strip()
        student_class = request.POST.get('student_class', '').strip()
        student_number = request.POST.get('student_number', '').strip()

        if not student_name or not student_class or not student_number:
            messages.error(request, 'กรุณากรอกข้อมูลให้ครบทุกช่อง')
            return render(request, 'reanBio/classroom_quiz_prestart.html', {
                'quiz': quiz,
                'student_name': student_name,
                'student_class': student_class,
                'student_number': student_number,
            })

        try:
            attempt = ClassroomQuizAttempt.objects.create(
                quiz=quiz, user=request.user, max_score=sum(q.points for q in questions),
                student_name=student_name, student_class=student_class, student_number=student_number,
            )
        except IntegrityError:
            # 🛑 กันกรณีกดส่งซ้ำ/เปิดสองแท็บพร้อมกันแล้วสร้างซ้ำ (unique_together กันไว้อีกชั้น)
            existing = ClassroomQuizAttempt.objects.filter(quiz=quiz, user=request.user).first()
            if existing:
                if existing.submitted_at:
                    return redirect('classroom_quiz_result', attempt_pk=existing.pk)
                return redirect('classroom_quiz_take', attempt_pk=existing.pk)
            raise

        for i, q in enumerate(questions, start=1):
            ClassroomQuizAnswer.objects.create(attempt=attempt, question=q, order=i)

        return redirect('classroom_quiz_take', attempt_pk=attempt.pk)

    return render(request, 'reanBio/classroom_quiz_prestart.html', {'quiz': quiz})


@login_required
def classroom_quiz_take_view(request, attempt_pk):
    attempt = get_object_or_404(ClassroomQuizAttempt, pk=attempt_pk, user=request.user)
    if attempt.submitted_at:
        return redirect('classroom_quiz_result', attempt_pk=attempt.pk)

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
        return redirect('classroom_quiz_result', attempt_pk=attempt.pk)

    return render(request, 'reanBio/classroom_quiz_take.html', {'attempt': attempt, 'answers': answers})


@login_required
def classroom_quiz_result_view(request, attempt_pk):
    attempt = get_object_or_404(ClassroomQuizAttempt, pk=attempt_pk, user=request.user)
    answers = (
        attempt.answers.select_related('question', 'selected_choice')
        .prefetch_related('question__choices')
        .order_by('order')
    )
    return render(request, 'reanBio/classroom_quiz_result.html', {'attempt': attempt, 'answers': answers})


@login_required
def classroom_quiz_attempts_view(request, quiz_pk):
    """หน้ารายชื่อคนที่ทำแบบทดสอบนี้แล้ว พร้อมคะแนน สำหรับคุณครูตรวจสอบ"""
    quiz = get_object_or_404(ClassroomQuiz, pk=quiz_pk)
    if not _can_manage_classroom(request.user, quiz.classroom):
        return redirect('classroom_detail', code=quiz.classroom.code)

    attempts = (
        quiz.attempts.filter(submitted_at__isnull=False)
        .select_related('user')
        .order_by('-submitted_at')
    )
    return render(request, 'reanBio/classroom_quiz_attempts.html', {'quiz': quiz, 'attempts': attempts})


@login_required
def classroom_quiz_export_view(request, quiz_pk):
    """ส่งออกผลคะแนนของแบบทดสอบนี้เป็นไฟล์ CSV (เปิดหรืออิมพอร์ตเข้า Google Sheets/Excel ได้ทันที)"""
    quiz = get_object_or_404(ClassroomQuiz, pk=quiz_pk)
    if not _can_manage_classroom(request.user, quiz.classroom):
        return redirect('classroom_detail', code=quiz.classroom.code)

    attempts = (
        quiz.attempts.filter(submitted_at__isnull=False)
        .select_related('user')
        .order_by('-submitted_at')
    )

    safe_title = "".join(c for c in quiz.title if c.isalnum() or c in (" ", "_", "-")).strip() or "quiz"
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{safe_title}_results.csv"'
    response.write('﻿')  # BOM ให้โปรแกรมอย่าง Excel อ่านภาษาไทยถูกต้อง

    writer = csv.writer(response)
    writer.writerow(['ชื่อ-นามสกุล', 'ชั้น', 'เลขที่', 'ชื่อผู้ใช้', 'คะแนนที่ได้', 'คะแนนเต็ม', 'เปอร์เซ็นต์', 'วันเวลาที่ส่งคำตอบ'])
    for attempt in attempts:
        display_name = attempt.student_name or attempt.user.first_name or attempt.user.username
        writer.writerow([
            display_name,
            attempt.student_class,
            attempt.student_number,
            attempt.user.username,
            attempt.score,
            attempt.max_score,
            attempt.percent,
            attempt.submitted_at.strftime('%d/%m/%Y %H:%M'),
        ])
    return response


@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    # แยกการดึงข้อมูลห้องเรียนตามบทบาทผู้ใช้
    is_teacher = getattr(request.user, 'is_teacher', False)
    if is_teacher:
        classrooms = Classroom.objects.filter(teacher=request.user).order_by('-created_at')
    else:
        classrooms = request.user.joined_classrooms.all().order_by('-created_at')

    context = {
        'profile': user_profile,
        'classrooms': classrooms,
        # 📌 แท็บ "เข้าชมล่าสุด": บทเรียนที่เปิดดูล่าสุด (บันทึกไว้ตอนเข้า lesson_detail_view)
        'recent_views': LessonView.objects.filter(user=request.user).select_related('lesson')[:10],
    }
    # 📌 แท็บ "แดชบอร์ด" ในหน้าโปรไฟล์: สรุปคะแนนแบบฝึกหัด/ข้อสอบ (เฉพาะนักเรียน คุณครูมีแดชบอร์ดห้องเรียนแยกต่างหาก)
    if not is_teacher:
        context.update(_dashboard_context(request.user))

    return render(request, 'reanBio/profile.html', context)

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
    checkpoints = list(lesson.checkpoints.prefetch_related('choices').all())
    content_html = _render_content_html(lesson.content, search_query, checkpoints)
    # 📌 คุณครูใช้หน้านี้เพื่ออ่านเนื้อหาเท่านั้น ไม่มีสิทธิ์ทำแบบฝึกหัด/ข้อสอบ (นั่นเป็นของนักเรียน)
    is_teacher = request.user.is_authenticated and getattr(request.user, 'is_teacher', False)

    # 📌 บันทึกว่าเข้าชมบทเรียนนี้ล่าสุดเมื่อไหร่ ไว้แสดงในแท็บ "เข้าชมล่าสุด" ของหน้าโปรไฟล์
    if request.user.is_authenticated:
        LessonView.objects.update_or_create(user=request.user, lesson=lesson)

    return render(request, 'reanBio/lesson_detail.html', {
        'lesson': lesson,
        'content_html': content_html,
        'search_query': search_query,
        'is_teacher': is_teacher,
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
    """หน้าภาพรวมแบบฝึกหัดของบทเรียนหนึ่งๆ พร้อมประวัติการทำของผู้ใช้ และปุ่มเริ่มทำข้อสอบของหัวข้อนี้"""
    lesson = get_object_or_404(Lesson, pk=pk)
    # 🛑 คุณครูไม่มีสิทธิ์ทำแบบฝึกหัด/ข้อสอบ (ใช้บทเรียนสำหรับอ่านเนื้อหาเท่านั้น)
    if getattr(request.user, 'is_teacher', False):
        messages.info(request, "บทบาทคุณครูใช้สำหรับอ่านเนื้อหาบทเรียนเท่านั้น ไม่มีการทำแบบฝึกหัด/ข้อสอบ")
        return redirect('lesson_detail', pk=lesson.pk)
    questions = list(lesson.questions.all())
    history = Attempt.objects.filter(
        user=request.user, lesson=lesson, mode='practice', submitted_at__isnull=False
    ).order_by('-submitted_at')

    # 📌 ข้อสอบสุ่มคำถามจากคลังของ "บทเรียนนี้" (หัวข้อย่อยนี้) เท่านั้น ไม่ผสมกับหัวข้อย่อยอื่นในบทเดียวกัน
    # เพื่อให้ประวัติการทำข้อสอบของแต่ละหัวข้อย่อยแยกจากกันชัดเจน ไม่ไปโผล่ซ้ำในหน้าหัวข้ออื่น
    exam_pool_count = len(questions)
    exam_history = Attempt.objects.filter(
        user=request.user, mode='exam', lesson=lesson, submitted_at__isnull=False
    ).order_by('-submitted_at')

    return render(request, 'reanBio/lesson_exercise.html', {
        'lesson': lesson,
        'question_count': len(questions),
        'history': history,
        'exam_pool_count': exam_pool_count,
        'exam_history': exam_history,
    })


@login_required
def start_practice_attempt(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if getattr(request.user, 'is_teacher', False):
        messages.info(request, "บทบาทคุณครูใช้สำหรับอ่านเนื้อหาบทเรียนเท่านั้น ไม่มีการทำแบบฝึกหัด/ข้อสอบ")
        return redirect('lesson_detail', pk=lesson.pk)
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


def _create_exam_attempt(user, lesson, num_questions):
    """สุ่มคำถามจากคลังข้อสอบของ 'บทเรียนนี้' (หัวข้อย่อยนี้) เท่านั้น แล้วสร้าง Attempt แบบข้อสอบ
    คืนค่า Attempt หรือ None ถ้าไม่มีคำถามเลย"""
    pool = list(lesson.questions.all())
    if not pool:
        return None

    num_questions = max(1, min(num_questions, len(pool)))
    selected = random.sample(pool, num_questions)

    attempt = Attempt.objects.create(
        user=user, mode='exam', lesson=lesson, grade=lesson.grade, chapter=lesson.chapter,
        max_score=sum(q.points for q in selected),
    )
    for i, q in enumerate(selected, start=1):
        AttemptAnswer.objects.create(attempt=attempt, question=q, order=i)
    return attempt


@login_required
def start_lesson_exam(request, pk):
    """เริ่มทำข้อสอบแบบสุ่มจากคำถามของบทเรียน (หัวข้อย่อย) นี้เท่านั้น ริเริ่มจากหน้าบทเรียนโดยตรง"""
    lesson = get_object_or_404(Lesson, pk=pk)
    if getattr(request.user, 'is_teacher', False):
        messages.info(request, "บทบาทคุณครูใช้สำหรับอ่านเนื้อหาบทเรียนเท่านั้น ไม่มีการทำแบบฝึกหัด/ข้อสอบ")
        return redirect('lesson_detail', pk=lesson.pk)
    try:
        num_questions = int(request.POST.get('num_questions', 10))
    except ValueError:
        num_questions = 10

    attempt = _create_exam_attempt(request.user, lesson, num_questions)
    if attempt is None:
        messages.error(request, "หัวข้อนี้ยังไม่มีคำถามในคลังข้อสอบ")
        return redirect('lesson_exercise', pk=lesson.pk)

    return redirect('attempt_take', attempt_pk=attempt.pk)


# ============================================================
# 📌 ควิซอัจฉริยะ (AI Quiz Generator): สุ่มข้อสอบข้ามบทเรียน ตามระดับชั้น/บทที่ที่เลือก
# ============================================================
def _create_multi_lesson_exam_attempt(user, grade, chapter, num_questions):
    """สุ่มคำถามข้ามบทเรียนตามเงื่อนไขระดับชั้น/บทที่ที่เลือก แล้วสร้าง Attempt แบบข้อสอบรวม
    (ไม่ผูกกับบทเรียนเดียว lesson=None) คืนค่า Attempt หรือ None ถ้าไม่พบคำถามในขอบเขตที่เลือก"""
    pool = Question.objects.select_related('lesson')
    if grade in ['m4', 'm5', 'm6']:
        pool = pool.filter(lesson__grade=grade)
    if chapter:
        pool = pool.filter(lesson__chapter=chapter)
    pool = list(pool)
    if not pool:
        return None

    num_questions = max(1, min(num_questions, len(pool)))
    selected = random.sample(pool, num_questions)

    attempt = Attempt.objects.create(
        user=user, mode='exam',
        grade=grade if grade in ['m4', 'm5', 'm6'] else '',
        chapter=chapter,
        max_score=sum(q.points for q in selected),
    )
    for i, q in enumerate(selected, start=1):
        AttemptAnswer.objects.create(attempt=attempt, question=q, order=i)
    return attempt


def quiz_generator_view(request):
    """หน้าตั้งค่าสร้างแบบทดสอบอัตโนมัติ: เลือกระดับชั้น/บทที่/จำนวนข้อ แล้วสุ่มคำถามข้ามบทเรียนให้ทันที"""
    return render(request, 'reanBio/quiz_generator.html', {
        'chapters_by_grade_json': json.dumps(_chapters_by_grade()),
        'total_questions': Question.objects.count(),
    })


@login_required
def start_generated_quiz(request):
    if request.method != 'POST':
        return redirect('quiz_generator')
    if getattr(request.user, 'is_teacher', False):
        messages.info(request, "บทบาทคุณครูใช้สำหรับอ่านเนื้อหาบทเรียนเท่านั้น ไม่มีการทำแบบฝึกหัด/ข้อสอบ")
        return redirect('quiz_generator')

    grade = request.POST.get('grade', 'all')
    chapter_raw = request.POST.get('chapter', '').strip()
    chapter = int(chapter_raw) if chapter_raw.isdigit() else None
    try:
        num_questions = int(request.POST.get('num_questions', 10))
    except ValueError:
        num_questions = 10

    attempt = _create_multi_lesson_exam_attempt(request.user, grade, chapter, num_questions)
    if attempt is None:
        messages.error(request, "ไม่พบคำถามในขอบเขตที่เลือก กรุณาเลือกระดับชั้น/บทที่ใหม่")
        return redirect('quiz_generator')

    return redirect('attempt_take', attempt_pk=attempt.pk)


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

    # สำหรับผลข้อสอบ (exam mode): หาบทเรียนของหัวข้อนั้นๆ เพื่อใช้เป็นทางลัดกลับไป "ทำข้อสอบอีกครั้ง"
    # (ข้อสอบผูกกับบทเรียนโดยตรงอยู่แล้ว ยกเว้นข้อสอบรุ่นเก่าก่อนเปลี่ยนมาผูกกับหัวข้อย่อยที่ยังไม่ถูก backfill)
    retake_lesson = None
    if attempt.mode == 'exam':
        if attempt.lesson:
            retake_lesson = attempt.lesson
        else:
            lessons_qs = Lesson.objects.filter(grade=attempt.grade or 'm4')
            if attempt.chapter:
                lessons_qs = lessons_qs.filter(chapter=attempt.chapter)
            retake_lesson = lessons_qs.first()

    return render(request, 'reanBio/attempt_result.html', {
        'attempt': attempt,
        'answers': answers,
        'retake_lesson': retake_lesson,
        'retake_num_questions': answers.count(),
    })


def _dashboard_context(user):
    """สรุปประวัติคะแนนแบบฝึกหัด/ข้อสอบของผู้ใช้ สำหรับแสดงในแท็บ 'แดชบอร์ด' ของหน้าโปรไฟล์"""
    attempts = list(
        Attempt.objects.filter(user=user, submitted_at__isnull=False)
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

    # 📌 คะแนนรวมถ่วงน้ำหนักแบบ GPA: ใช้คะแนนข้อสอบ "ล่าสุด" ของแต่ละหัวข้อย่อย คูณน้ำหนัก (credit_weight)
    # ของหัวข้อนั้น แล้วหารด้วยผลรวมน้ำหนัก เหมือนเกรดเฉลี่ยที่แต่ละวิชามีหน่วยกิตไม่เท่ากัน
    latest_exam_by_lesson = {}
    for a in exam_attempts:  # exam_attempts เรียงจากเก่า -> ใหม่อยู่แล้ว ตัวหลังจะทับตัวก่อนหน้า เหลือแค่ครั้งล่าสุด
        if a.lesson_id:
            latest_exam_by_lesson[a.lesson_id] = a

    weighted_rows = []
    total_weight = 0.0
    weighted_sum = 0.0
    for a in latest_exam_by_lesson.values():
        weight = a.lesson.credit_weight
        weighted_rows.append({
            'lesson': a.lesson,
            'percent': a.percent,
            'weight': weight,
            'submitted_at': a.submitted_at,
            'attempt_pk': a.pk,
        })
        total_weight += weight
        weighted_sum += a.percent * weight
    weighted_rows.sort(key=lambda r: (r['lesson'].chapter, r['lesson'].subtopic_code))
    weighted_overall = round(weighted_sum / total_weight, 1) if total_weight else None

    return {
        'practice_attempts': list(reversed(practice_attempts)),
        'exam_attempts': list(reversed(exam_attempts)),
        'practice_series': series(practice_attempts),
        'exam_series': series(exam_attempts),
        'practice_trend': trend(practice_attempts),
        'exam_trend': trend(exam_attempts),
        'total_attempts': len(attempts),
        'weighted_overall': weighted_overall,
        'weighted_rows': weighted_rows,
        'weighted_total': round(total_weight, 1) if total_weight else None,
    }


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
