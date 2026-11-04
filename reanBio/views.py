# 📌 Views สำหรับโปรเจกต์ reanBio (โหมด Mockup 100% — ไม่ใช้ฐานข้อมูล และไม่ต้องสมัครสมาชิกจริง)
# ทุกหน้าและทุกปุ่มทำงานผ่านข้อมูลจำลองในหน่วยความจำ (mock_data.py)

import csv
import json
import re
from datetime import datetime
from itertools import groupby

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.html import escape

from .ai_helper import ask_biology_ai, ask_biology_tutor_chat, AskAIError
from .mock_data import (
    MOCK_STUDENT, MOCK_STUDENT_2, MOCK_STUDENT_3, MOCK_TEACHER, MOCK_GUEST,
    MOCK_CLASSROOMS, MOCK_FLASHCARD_DECKS, MOCK_ATTEMPTS, MOCK_CHAT_SESSIONS,
    MockBioChatSession, MockBioChatMessage, MockAttempt, MockAttemptAnswer,
    TUTOR_MODE_CHOICES, get_mock_lessons, get_mock_lesson, get_mock_classroom,
)


def _highlight(text, query):
    escaped_text = escape(text)
    if not query:
        return escaped_text
    pattern = re.compile(re.escape(escape(query)), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark class='bg-yellow-200 rounded px-0.5'>{m.group(0)}</mark>", escaped_text)


def _render_checkpoint_html(checkpoint):
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


def home(request):
    return render(request, 'index.html')


# ============================================================
# 📌 1. ระบบสลับบทบาท Mockup ด้วยปุ่มกด (ไม่ต้องสมัครสมาชิกจริง)
# ============================================================

def signup(request):
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('home')
    role = request.GET.get('role') or request.POST.get('role')
    if request.method == 'POST' or role in ('student', 'teacher'):
        chosen_role = role if role in ('student', 'teacher') else 'student'
        target = reverse('teacher_dashboard') if chosen_role == 'teacher' else next_url
        resp = redirect(target)
        resp.set_cookie('reanbio_mock_role', chosen_role, max_age=86400 * 30)
        messages.success(
            request,
            f"เข้าใช้งานโหมด Mockup ในฐานะ {'คุณครู (ครูวิภา ชีววิทยา)' if chosen_role == 'teacher' else 'นักเรียน (สมชาย สายวิทย์ ม.4/1)'} เรียบร้อยแล้ว!"
        )
        return resp
    return render(request, 'reanBio/signup.html', {'next': next_url})


def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('home')
    role = request.GET.get('role') or request.POST.get('role')
    if request.method == 'POST' or role in ('student', 'teacher'):
        chosen_role = role if role in ('student', 'teacher') else 'student'
        target = reverse('teacher_dashboard') if chosen_role == 'teacher' else next_url
        resp = redirect(target)
        resp.set_cookie('reanbio_mock_role', chosen_role, max_age=86400 * 30)
        messages.success(
            request,
            f"เข้าสู่ระบบโหมด Mockup ในฐานะ {'คุณครู (ครูวิภา ชีววิทยา)' if chosen_role == 'teacher' else 'นักเรียน (สมชาย สายวิทย์ ม.4/1)'} เรียบร้อยแล้ว!"
        )
        return resp
    return render(request, 'reanBio/login.html', {'next': next_url})


def user_logout(request):
    resp = redirect('home')
    resp.set_cookie('reanbio_mock_role', 'guest', max_age=86400 * 30)
    messages.info(request, "สลับเป็นโหมดผู้เยี่ยมชม (ยังไม่ได้เข้าสู่ระบบ) เรียบร้อยแล้ว — กดปุ่มเลือกโหมดนักเรียน/คุณครูได้ตลอดเวลา")
    return resp


def student_info_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('my_classrooms')
    if request.method == 'POST':
        messages.success(request, "บันทึกข้อมูลนักเรียน (Mockup) เรียบร้อยแล้ว")
        return redirect(next_url)
    return render(request, 'reanBio/student_info_form.html', {
        'full_name': request.user.userprofile.full_name,
        'student_class': request.user.userprofile.student_class,
        'student_number': request.user.userprofile.student_number,
        'next': next_url,
    })


# ============================================================
# 📌 2. แชทบอทติวเตอร์ชีววิทยาอัจฉริยะ (Smart Biology AI Tutor)
# ============================================================

def ask_ai_view(request, session_pk=None):
    ai_question = ''
    ai_answer = ''
    ai_error = ''
    ai_sources = []

    bio_lessons = get_mock_lessons(subject='bio')
    valid_modes = dict(TUTOR_MODE_CHOICES)
    is_new_requested = request.GET.get('new') == '1'

    target_session_id = session_pk or request.POST.get('session_id') or request.GET.get('session_id')
    current_session = None
    if target_session_id and str(target_session_id).isdigit():
        sid = int(target_session_id)
        current_session = next((s for s in MOCK_CHAT_SESSIONS if s.pk == sid), None)
    elif not is_new_requested and MOCK_CHAT_SESSIONS and not request.GET.get('lesson'):
        current_session = MOCK_CHAT_SESSIONS[0]

    selected_lesson = current_session.lesson if current_session else None
    lesson_param = request.POST.get('lesson_id') if request.method == 'POST' else request.GET.get('lesson')
    if lesson_param is not None:
        if str(lesson_param).strip().isdigit():
            selected_lesson = get_mock_lesson(int(lesson_param))
        elif request.method == 'POST' and lesson_param == '':
            selected_lesson = None

    selected_mode = current_session.tutor_mode if current_session else 'explain'
    mode_param = request.POST.get('tutor_mode') or request.GET.get('mode')
    if mode_param in valid_modes:
        selected_mode = mode_param

    if request.method == 'POST':
        ai_question = request.POST.get('ai_question', '').strip()
        try:
            prior_history = []
            if current_session is not None:
                prior_history = [
                    {'role': m.role, 'content': m.content}
                    for m in current_session.messages.all()
                ]

            result = ask_biology_tutor_chat(
                question=ai_question,
                history=prior_history,
                lesson=selected_lesson,
                tutor_mode=selected_mode,
            )
            ai_answer = result['answer']
            ai_sources = result['sources']

            if current_session is None:
                new_pk = (max((s.pk for s in MOCK_CHAT_SESSIONS), default=0) + 1)
                short_title = ai_question[:60] + ('…' if len(ai_question) > 60 else '')
                current_session = MockBioChatSession(
                    pk=new_pk,
                    title=short_title or "บทสนทนาชีววิทยา",
                    lesson=selected_lesson,
                    tutor_mode=selected_mode,
                    messages=[],
                )
                MOCK_CHAT_SESSIONS.insert(0, current_session)
            else:
                current_session.lesson = selected_lesson
                current_session.tutor_mode = selected_mode

            current_session.messages._items.append(MockBioChatMessage('user', ai_question))
            current_session.messages._items.append(
                MockBioChatMessage('assistant', ai_answer, sources=ai_sources, engine=result.get('engine', 'local_bio_rag'))
            )
        except AskAIError as exc:
            ai_error = str(exc)

    chat_messages = current_session.messages.all() if current_session else []

    return render(request, 'reanBio/ask_ai.html', {
        'ai_question': '' if ai_answer else ai_question,
        'last_question': ai_question,
        'ai_answer': ai_answer,
        'ai_error': ai_error,
        'ai_sources': ai_sources,
        'current_session': current_session,
        'sessions': MOCK_CHAT_SESSIONS,
        'chat_messages': chat_messages,
        'bio_lessons': bio_lessons,
        'selected_lesson': selected_lesson,
        'selected_mode': selected_mode,
        'tutor_modes': TUTOR_MODE_CHOICES,
        'kb_doc_count': 2,
        'has_api_key': bool(getattr(settings, 'ANTHROPIC_API_KEY', '')),
    })


def bio_tutor_new_session_view(request):
    lesson_id = request.GET.get('lesson') or request.POST.get('lesson_id') or ''
    mode = request.GET.get('mode') or request.POST.get('tutor_mode') or 'explain'
    url = reverse('ask_ai') + f"?new=1&mode={mode}"
    if str(lesson_id).isdigit():
        url += f"&lesson={lesson_id}"
    return redirect(url)


def bio_tutor_delete_session_view(request, session_pk):
    if request.method == 'POST':
        MOCK_CHAT_SESSIONS[:] = [s for s in MOCK_CHAT_SESSIONS if s.pk != int(session_pk)]
        messages.success(request, 'ลบประวัติบทสนทนาชีววิทยา (Mockup) เรียบร้อยแล้ว')
    return redirect(f"{reverse('ask_ai')}?new=1")


def ai_feedback_view(request):
    return JsonResponse({'ok': True})


# ============================================================
# 📌 3. คลังบทเรียน & หน้าอ่านบทเรียน
# ============================================================

def lessons_view(request):
    grade_filter = request.GET.get('grade', 'all')
    search_query = request.GET.get('q', '').strip()

    lessons_list = get_mock_lessons(subject='bio', grade=grade_filter)
    filtered = []
    for l in lessons_list:
        l.search_snippet = ""
        if search_query:
            q_low = search_query.lower()
            if q_low not in l.title.lower() and q_low not in l.description.lower() and q_low not in l.content.lower():
                continue
            l.search_snippet = _build_content_snippet(l.content, search_query)
        filtered.append(l)

    chapter_groups = []
    for ch_num, group_iter in groupby(filtered, key=lambda x: x.chapter):
        group_items = list(group_iter)
        chapter_groups.append({
            'chapter': ch_num,
            'chapter_title': group_items[0].chapter_title if group_items else '',
            'lessons': group_items,
        })

    return render(request, 'reanBio/lessons.html', {
        'lessons': filtered,
        'chapter_groups': chapter_groups,
        'current_grade': grade_filter,
        'search_query': search_query,
    })


def lesson_detail_view(request, pk):
    lesson = get_mock_lesson(pk) or get_mock_lessons(subject='bio')[0]
    search_query = request.GET.get('q', '').strip()
    checkpoints = lesson.checkpoints.all()
    content_html = _render_content_html(lesson.content, search_query, checkpoints)
    is_teacher = getattr(request.user, 'is_teacher', False)

    ai_question = ''
    ai_answer = ''
    ai_error = ''
    if request.method == 'POST':
        ai_question = request.POST.get('ai_question', '').strip()
        try:
            ai_answer = ask_biology_ai(ai_question, lesson=lesson)
        except AskAIError as exc:
            ai_error = str(exc)

    return render(request, 'reanBio/lesson_detail.html', {
        'lesson': lesson,
        'content_html': content_html,
        'search_query': search_query,
        'is_teacher': is_teacher,
        'ai_question': ai_question,
        'ai_answer': ai_answer,
        'ai_error': ai_error,
    })


# ============================================================
# 📌 4. หน้าโปรไฟล์ & แดชบอร์ดจำลอง
# ============================================================

def profile(request):
    bio_lessons = get_mock_lessons(subject='bio')
    practice_list = [a for a in MOCK_ATTEMPTS.values() if a.mode == 'practice']
    exam_list = [a for a in MOCK_ATTEMPTS.values() if a.mode == 'exam']

    weighted_rows = []
    for idx, l in enumerate(bio_lessons[:3], start=1):
        weighted_rows.append({
            'lesson': l,
            'weight': l.credit_weight,
            'percent': 85.0 if idx % 2 else 90.0,
            'attempt_pk': 2 if 2 in MOCK_ATTEMPTS else 1,
        })

    practice_series = [
        {'date': '18/09', 'percent': 70, 'label': 'ธรรมชาติของสิ่งมีชีวิต'},
        {'date': '20/09', 'percent': 85, 'label': 'เคมีที่เป็นพื้นฐานของสิ่งมีชีวิต'},
        {'date': '22/09', 'percent': 95, 'label': 'เซลล์ของสิ่งมีชีวิต'},
    ]
    exam_series = [
        {'date': '19/09', 'percent': 75, 'label': 'บทที่ 1 การศึกษาชีววิทยา'},
        {'date': '23/09', 'percent': 88, 'label': 'บทที่ 1 การศึกษาชีววิทยา'},
    ]

    video_views = [
        {
            'title': 'สรุปโครงสร้างและหน้าที่ของออร์แกเนลล์ในเซลล์ (3D Animation)',
            'classroom_name': MOCK_CLASSROOMS[0].name,
            'viewed_at': datetime(2026, 9, 22, 16, 30),
            'url': reverse('classroom_video_watch', kwargs={'code': MOCK_CLASSROOMS[0].code, 'video_pk': 1}),
        }
    ]
    recent_views = [
        {
            'icon': '📘',
            'title': bio_lessons[0].title if bio_lessons else 'บทเรียนชีววิทยา',
            'subtitle': 'เปิดอ่านบทเรียน ม.4 · บทที่ 1',
            'viewed_at': datetime(2026, 9, 23, 10, 15),
            'url': reverse('lesson_detail', kwargs={'pk': bio_lessons[0].pk if bio_lessons else 1}),
        },
        {
            'icon': '🗂️',
            'title': 'การ์ดคำศัพท์คลังกลาง',
            'subtitle': 'ทบทวนคำศัพท์ออร์แกเนลล์ ม.4',
            'viewed_at': datetime(2026, 9, 22, 19, 40),
            'url': reverse('flashcards'),
        },
    ]

    return render(request, 'reanBio/profile.html', {
        'classrooms': MOCK_CLASSROOMS,
        'video_views': video_views,
        'recent_views': recent_views,
        'total_attempts': len(MOCK_ATTEMPTS),
        'weighted_overall': 87.5,
        'weighted_total': 3.5,
        'weighted_rows': weighted_rows,
        'practice_trend': 15.0,
        'exam_trend': 13.0,
        'practice_series': json.dumps(practice_series, ensure_ascii=False),
        'exam_series': json.dumps(exam_series, ensure_ascii=False),
        'practice_attempts': practice_list,
        'exam_attempts': exam_list,
    })


# ============================================================
# 📌 5. ห้องเรียนของนักเรียน & แดชบอร์ดคุณครู (Mockup)
# ============================================================

def my_classroom_view(request):
    if getattr(request.user, 'is_teacher', False):
        return redirect('teacher_dashboard')
    return render(request, 'reanBio/my_classrooms.html', {'classrooms': MOCK_CLASSROOMS})


def join_classroom_view(request):
    code = (request.POST.get('code') or request.GET.get('code') or 'BIO101').strip().upper()
    messages.success(request, f"เข้าร่วมห้องเรียนรหัส {code} (โหมด Mockup) เรียบร้อยแล้ว!")
    return redirect('classroom_detail', code=code)


def teacher_dashboard_view(request):
    if request.method == 'POST':
        messages.success(request, "จำลองการสร้างห้องเรียนใหม่ (โหมด Mockup) เรียบร้อยแล้ว!")
    return render(request, 'reanBio/teacher_dashboard.html', {'classrooms': MOCK_CLASSROOMS})


def classroom_detail_view(request, code):
    room = get_mock_classroom(code)
    return render(request, 'reanBio/classroom_detail.html', {
        'classroom': room,
        'is_owner': getattr(request.user, 'is_teacher', False),
        'videos': room.videos.all(),
        'files': room.files.all(),
        'quizzes': room.quizzes.all(),
    })


def classroom_edit_view(request, code):
    room = get_mock_classroom(code)
    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            room.name = new_name
        messages.success(request, f"อัปเดตชื่อห้องเรียนเป็น '{room.name}' (Mockup) เรียบร้อยแล้ว")
        return redirect('classroom_detail', code=room.code)
    return render(request, 'reanBio/classroom_edit.html', {'classroom': room})


def classroom_delete_view(request, code):
    room = get_mock_classroom(code)
    if request.method == 'POST':
        messages.success(request, f"จำลองการลบห้องเรียน '{room.name}' (Mockup) เรียบร้อยแล้ว")
        return redirect('teacher_dashboard')
    return render(request, 'reanBio/classroom_confirm_delete.html', {'classroom': room})


def classroom_students_view(request, code):
    room = get_mock_classroom(code)
    search_query = request.GET.get('q', '').strip().lower()
    students = room.students.all()
    if search_query:
        students = [
            s for s in students
            if search_query in s.username.lower() or search_query in s.userprofile.full_name.lower()
        ]
    return render(request, 'reanBio/classroom_students.html', {
        'classroom': room,
        'students': students,
        'total_students': len(room.students),
        'search_query': request.GET.get('q', '').strip(),
        'is_owner': True,
    })


def classroom_remove_student_view(request, code, student_pk):
    room = get_mock_classroom(code)
    messages.success(request, "จำลองการคัดนักเรียนออกจากห้องเรียน (Mockup) เรียบร้อยแล้ว")
    return redirect('classroom_students', code=room.code)


def classroom_students_export_view(request, code):
    room = get_mock_classroom(code)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="students_{room.code}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['ลำดับ', 'ชื่อผู้ใช้ (Username)', 'ชื่อ-นามสกุล', 'ชั้น', 'เลขที่', 'อีเมล'])
    for idx, s in enumerate(room.students.all(), start=1):
        writer.writerow([idx, s.username, s.userprofile.full_name, s.userprofile.student_class, s.userprofile.student_number, s.email])
    return response


def classroom_video_watch_view(request, code, video_pk):
    room = get_mock_classroom(code)
    video = next((v for v in room.videos.all() if v.pk == int(video_pk)), room.videos.first())
    return render(request, 'reanBio/classroom_video_watch.html', {
        'classroom': room,
        'video': video,
    })


def classroom_add_video_view(request, code):
    room = get_mock_classroom(code)
    if request.method == 'POST':
        messages.success(request, "จำลองการเพิ่มคลิปวิดีโอเข้าห้องเรียน (Mockup) เรียบร้อยแล้ว")
        return redirect('classroom_detail', code=room.code)
    return render(request, 'reanBio/classroom_add_video.html', {'classroom': room})


def classroom_add_file_view(request, code):
    room = get_mock_classroom(code)
    if request.method == 'POST':
        messages.success(request, "จำลองการอัปโหลดไฟล์เอกสารเข้าห้องเรียน (Mockup) เรียบร้อยแล้ว")
        return redirect('classroom_detail', code=room.code)
    return render(request, 'reanBio/classroom_add_file.html', {'classroom': room})


def classroom_add_quiz_view(request, code):
    room = get_mock_classroom(code)
    if request.method == 'POST':
        messages.success(request, "จำลองการสร้างแบบทดสอบเข้าห้องเรียน (Mockup) เรียบร้อยแล้ว")
        return redirect('classroom_detail', code=room.code)
    return render(request, 'reanBio/classroom_add_quiz.html', {'classroom': room})


def classroom_quiz_start_view(request, quiz_pk):
    room = MOCK_CLASSROOMS[0]
    quiz = room.quizzes.first()
    if request.method == 'POST':
        return redirect('classroom_quiz_take', attempt_pk=1)
    return render(request, 'reanBio/classroom_quiz_prestart.html', {
        'quiz': quiz,
        'classroom': room,
        'initial_name': request.user.userprofile.full_name,
        'initial_class': request.user.userprofile.student_class,
        'initial_number': request.user.userprofile.student_number,
    })


def classroom_quiz_take_view(request, attempt_pk):
    room = MOCK_CLASSROOMS[0]
    quiz = room.quizzes.first()
    attempt = quiz.attempts.first()
    default_att = MOCK_ATTEMPTS.get(1)
    answers = default_att.answers.all() if default_att else []
    if request.method == 'POST':
        return redirect('classroom_quiz_result', attempt_pk=attempt_pk)
    return render(request, 'reanBio/classroom_quiz_take.html', {
        'attempt': attempt,
        'quiz': quiz,
        'classroom': room,
        'answers': answers,
    })


def classroom_quiz_result_view(request, attempt_pk):
    room = MOCK_CLASSROOMS[0]
    quiz = room.quizzes.first()
    attempt = quiz.attempts.first()
    default_att = MOCK_ATTEMPTS.get(1)
    answers = default_att.answers.all() if default_att else []
    return render(request, 'reanBio/classroom_quiz_result.html', {
        'attempt': attempt,
        'quiz': quiz,
        'classroom': room,
        'answers': answers,
    })


def classroom_quiz_attempts_view(request, quiz_pk):
    room = MOCK_CLASSROOMS[0]
    quiz = room.quizzes.first()
    return render(request, 'reanBio/classroom_quiz_attempts.html', {
        'quiz': quiz,
        'classroom': room,
        'attempts': quiz.attempts.all(),
    })


def classroom_quiz_export_view(request, quiz_pk):
    room = MOCK_CLASSROOMS[0]
    quiz = room.quizzes.first()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="quiz_{quiz.pk}_scores.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['ชื่อ-นามสกุล', 'ชั้น', 'เลขที่', 'คะแนน', 'คะแนนเต็ม', 'เปอร์เซ็นต์'])
    for a in quiz.attempts.all():
        writer.writerow([a.student_name, a.student_class, a.student_number, a.score, a.max_score, f"{a.percent}%"])
    return response


# ============================================================
# 📌 6. การ์ดคำศัพท์ (Flashcards Mockup)
# ============================================================

def flashcards_view(request):
    grade_filter = request.GET.get('grade', 'all')
    chapter_filter = request.GET.get('chapter', '')

    bio_lessons = get_mock_lessons(subject='bio', grade=grade_filter)
    available_chapters = sorted({l.chapter for l in bio_lessons})

    cards = []
    for l in bio_lessons:
        if chapter_filter and str(l.chapter) != str(chapter_filter):
            continue
        for q in l.questions.all():
            correct = next((c.text for c in q.choices.all() if c.is_correct), "")
            if not correct and q.accepted_answers:
                correct = ", ".join(q.accepted_answers)
            back_text = f"คำตอบ: {correct}"
            if q.explanation:
                back_text += f"\n\nคำอธิบาย: {q.explanation}"
            cards.append({
                'front': q.text,
                'back': back_text,
                'lesson': f"{l.get_grade_display()} · {l.title}",
            })

    return render(request, 'reanBio/flashcards.html', {
        'cards_json': json.dumps(cards, ensure_ascii=False),
        'card_count': len(cards),
        'current_grade': grade_filter,
        'current_chapter': chapter_filter,
        'available_chapters': available_chapters,
        'my_decks': MOCK_FLASHCARD_DECKS,
        'show_my_decks_tab': not getattr(request.user, 'is_teacher', False),
    })


def my_flashcards_view(request):
    if request.method == 'POST':
        messages.success(request, "จำลองการสร้างชุดการ์ดคำศัพท์ใหม่ (Mockup) เรียบร้อยแล้ว!")
    return redirect(f"{reverse('flashcards')}?tab=mine")


def flashcard_deck_detail_view(request, deck_pk):
    deck = next((d for d in MOCK_FLASHCARD_DECKS if d.pk == int(deck_pk)), MOCK_FLASHCARD_DECKS[0])
    if request.method == 'POST':
        messages.success(request, "จำลองการเพิ่มการ์ดคำศัพท์ใหม่ (Mockup) เรียบร้อยแล้ว!")
    return render(request, 'reanBio/flashcard_deck_detail.html', {
        'deck': deck,
        'cards': deck.cards.all(),
    })


def flashcard_deck_delete_view(request, deck_pk):
    messages.success(request, "จำลองการลบชุดการ์ดคำศัพท์ (Mockup) เรียบร้อยแล้ว!")
    return redirect(f"{reverse('flashcards')}?tab=mine")


def flashcard_deck_study_view(request, deck_pk):
    deck = next((d for d in MOCK_FLASHCARD_DECKS if d.pk == int(deck_pk)), MOCK_FLASHCARD_DECKS[0])
    cards_data = [{'front': c.front, 'back': c.back} for c in deck.cards.all()]
    return render(request, 'reanBio/flashcard_deck_study.html', {
        'deck': deck,
        'cards_json': json.dumps(cards_data, ensure_ascii=False),
        'card_count': len(cards_data),
    })


def flashcard_card_delete_view(request, card_pk):
    messages.success(request, "จำลองการลบการ์ดคำศัพท์ (Mockup) เรียบร้อยแล้ว!")
    return redirect('flashcard_deck_detail', deck_pk=1)


# ============================================================
# 📌 7. สร้างแบบทดสอบ & ทำแบบฝึกหัด/ข้อสอบ (Mockup)
# ============================================================

def quiz_generator_view(request):
    bio_lessons = get_mock_lessons(subject='bio')
    total_q = sum(len(l.questions) for l in bio_lessons)
    chapters_by_grade = {'m4': [1], 'm5': [], 'm6': []}
    return render(request, 'reanBio/quiz_generator.html', {
        'total_questions': total_q,
        'chapters_by_grade_json': json.dumps(chapters_by_grade),
    })


def start_generated_quiz(request):
    return redirect('attempt_take', attempt_pk=2)


def lesson_exercise_view(request, pk):
    lesson = get_mock_lesson(pk) or get_mock_lessons(subject='bio')[0]
    q_count = len(lesson.questions)
    practice_hist = [a for a in MOCK_ATTEMPTS.values() if a.mode == 'practice']
    exam_hist = [a for a in MOCK_ATTEMPTS.values() if a.mode == 'exam']
    return render(request, 'reanBio/lesson_exercise.html', {
        'lesson': lesson,
        'question_count': q_count,
        'exam_pool_count': q_count,
        'history': practice_hist,
        'exam_history': exam_hist,
    })


def start_practice_attempt(request, pk):
    return redirect('attempt_take', attempt_pk=1)


def start_lesson_exam(request, pk):
    return redirect('attempt_take', attempt_pk=2)


def exercise_pdf_view(request, pk):
    lesson = get_mock_lesson(pk) or get_mock_lessons(subject='bio')[0]
    messages.info(request, f"โหมด Mockup: จำลองการดาวน์โหลดไฟล์ PDF แบบฝึกหัด '{lesson.title}'")
    return redirect('lesson_exercise', pk=lesson.pk)


def attempt_take_view(request, attempt_pk):
    attempt = MOCK_ATTEMPTS.get(int(attempt_pk)) or next(iter(MOCK_ATTEMPTS.values()))
    if request.method == 'POST':
        messages.success(request, "ส่งคำตอบเรียบร้อยแล้ว! นี่คือผลคะแนนจำลองของคุณ (Mockup)")
        return redirect('attempt_result', attempt_pk=attempt.pk)
    return render(request, 'reanBio/attempt_take.html', {
        'attempt': attempt,
        'answers': attempt.answers.all(),
    })


def attempt_result_view(request, attempt_pk):
    attempt = MOCK_ATTEMPTS.get(int(attempt_pk)) or next(iter(MOCK_ATTEMPTS.values()))
    return render(request, 'reanBio/attempt_result.html', {
        'attempt': attempt,
        'answers': attempt.answers.all(),
    })
