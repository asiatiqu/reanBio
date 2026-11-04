# 📌 ระบบข้อมูลจำลอง (In-Memory Mock Data & Mock Auth Middleware) สำหรับโปรเจกต์ reanBio
# ทำงานโดยไม่ต้องใช้ฐานข้อมูล (Database-free Mockup) และไม่ต้องสมัครสมาชิกจริง

import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SEED_FILE = BASE_DIR / 'mock_seed_data.json'

GRADE_DISPLAY = {
    'm4': 'ม.4',
    'm5': 'ม.5',
    'm6': 'ม.6',
}

SUBJECT_DISPLAY = {
    'bio': 'ชีววิทยา',
    'english': 'ภาษาอังกฤษ',
}

TUTOR_MODE_CHOICES = (
    ('explain', '📖 อธิบายละเอียดเข้าใจง่าย'),
    ('exam_prep', '🎯 ติวเข้มเน้นจุดออกสอบ'),
    ('socratic', '🧠 ชวนคิดวิเคราะห์ทีละขั้น'),
    ('summary', '⚡ สรุปย่อ & เทคนิคช่วยจำ'),
)
TUTOR_MODE_DISPLAY = dict(TUTOR_MODE_CHOICES)


class MockListManager:
    """เลียนแบบ RelatedManager ของ Django เช่น .all(), .count(), .first() บนลิสต์ในหน่วยความจำ"""
    def __init__(self, items=None):
        self._items = list(items or [])

    def all(self):
        return list(self._items)

    def count(self):
        return len(self._items)

    def first(self):
        return self._items[0] if self._items else None

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __bool__(self):
        return True


class MockUserProfile:
    def __init__(self, full_name="สมชาย สายวิทย์", student_class="ม.4/1", student_number="15", grade="m4"):
        self.full_name = full_name
        self.student_class = student_class
        self.student_number = student_number
        self.grade = grade
        self.avatar = None

    @property
    def has_student_info(self):
        return True


class MockUser:
    def __init__(self, pk=1, username="student_demo", first_name="สมชาย", last_name="สายวิทย์",
                 email="student@reanbio.mockup", role="student", is_authenticated=True,
                 full_name="สมชาย สายวิทย์", student_class="ม.4/1", student_number="15"):
        self.pk = pk
        self.id = pk
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role
        self.is_authenticated = is_authenticated
        self.is_anonymous = not is_authenticated
        self.userprofile = MockUserProfile(
            full_name=full_name,
            student_class=student_class,
            student_number=student_number,
        )

    @property
    def is_teacher(self):
        return self.is_authenticated and self.role == 'teacher'

    @property
    def is_student(self):
        return self.is_authenticated and self.role == 'student'

    def __str__(self):
        return self.username

    def __eq__(self, other):
        return isinstance(other, MockUser) and self.pk == other.pk and self.is_authenticated == other.is_authenticated


# 📌 ผู้ใช้งานจำลอง (นักเรียน / คุณครู / ผู้เยี่ยมชม)
MOCK_STUDENT = MockUser(
    pk=1,
    username="student_bio",
    first_name="สมชาย",
    last_name="สายวิทย์",
    role="student",
    is_authenticated=True,
    full_name="สมชาย สายวิทย์",
    student_class="ม.4/1",
    student_number="15",
)

MOCK_STUDENT_2 = MockUser(
    pk=2,
    username="student_m4_2",
    first_name="กมลชนก",
    last_name="รักชีวะ",
    role="student",
    is_authenticated=True,
    full_name="กมลชนก รักชีวะ",
    student_class="ม.4/1",
    student_number="8",
)

MOCK_STUDENT_3 = MockUser(
    pk=3,
    username="student_m4_3",
    first_name="ธนภัทร",
    last_name="เก่งวิทย์",
    role="student",
    is_authenticated=True,
    full_name="ธนภัทร เก่งวิทย์",
    student_class="ม.4/2",
    student_number="21",
)

MOCK_TEACHER = MockUser(
    pk=10,
    username="teacher_wipa",
    first_name="ครูวิภา",
    last_name="ชีววิทยา",
    role="teacher",
    is_authenticated=True,
    full_name="ครูวิภา ชีววิทยา",
    student_class="-",
    student_number="-",
)

MOCK_GUEST = MockUser(
    pk=0,
    username="guest",
    first_name="ผู้เยี่ยมชม",
    last_name="",
    role="student",
    is_authenticated=False,
)


class MockAuthMiddleware:
    """Middleware จำลองสถานะผู้ใช้จาก Cookie 'mock_role' โดยไม่ใช้ฐานข้อมูล
    ค่าเริ่มต้นคือ 'student' เพื่อให้เปิดเว็บมาแล้วกดดูทุกฟีเจอร์ได้ทันที และสลับเป็น 'teacher' หรือ 'guest' ได้ด้วยปุ่มเดียว"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        role_Switch = request.GET.get('mock_role')
        role = role_Switch or request.COOKIES.get('reanbio_mock_role', 'student')

        if role == 'teacher':
            request.user = MOCK_TEACHER
        elif role == 'guest':
            request.user = MOCK_GUEST
        else:
            role = 'student'
            request.user = MOCK_STUDENT

        request.mock_role = role
        response = self.get_response(request)
        if role_Switch in ('student', 'teacher', 'guest'):
            response.set_cookie('reanbio_mock_role', role_Switch, max_age=86400 * 30)
        return response


class MockChoice:
    def __init__(self, pk, order, text, is_correct):
        self.pk = pk
        self.id = pk
        self.order = order
        self.text = text
        self.is_correct = is_correct


class MockCheckpoint:
    def __init__(self, pk, after_paragraph, order, text, explanation, choices):
        self.pk = pk
        self.id = pk
        self.after_paragraph = after_paragraph
        self.order = order
        self.text = text
        self.explanation = explanation
        self.choices = MockListManager([MockChoice(**c) for c in choices])


class MockQuestion:
    def __init__(self, pk, lesson, order, question_type, text, explanation, points, accepted_answers, choices):
        self.pk = pk
        self.id = pk
        self.lesson = lesson
        self.order = order
        self.question_type = question_type
        self.text = text
        self.explanation = explanation
        self.points = points
        self.accepted_answers = accepted_answers or []
        self.choices = MockListManager([MockChoice(**c) for c in choices])


class MockLesson:
    def __init__(self, raw):
        self.pk = raw['pk']
        self.id = raw['pk']
        self.title = raw['title']
        self.subject = raw.get('subject', 'bio')
        self.grade = raw.get('grade', 'm4')
        self.icon = raw.get('icon', '🧬')
        self.description = raw.get('description', '')
        self.content = raw.get('content', '')
        self.diagram_svg = raw.get('diagram_svg', '')
        self.chapter = raw.get('chapter', 1)
        self.chapter_title = raw.get('chapter_title', '')
        self.subtopic_code = raw.get('subtopic_code', '')
        self.sub_lessons_count = raw.get('sub_lessons_count', 1)
        self.duration_minutes = raw.get('duration_minutes', 30)
        self.order = raw.get('order', 1)
        self.credit_weight = raw.get('credit_weight', 1.0)
        self.search_snippet = ""

        q_objs = [MockQuestion(lesson=self, **q) for q in raw.get('questions', [])]
        cp_objs = [MockCheckpoint(**cp) for cp in raw.get('checkpoints', [])]
        self.questions = MockListManager(q_objs)
        self.checkpoints = MockListManager(cp_objs)

    def get_grade_display(self):
        return GRADE_DISPLAY.get(self.grade, self.grade)

    def get_subject_display(self):
        return SUBJECT_DISPLAY.get(self.subject, self.subject)


# 📌 โหลดข้อมูลบทเรียน คำถาม และ Checkpoint จากไฟล์ mock_seed_data.json เข้าสู่หน่วยความจำ
def _load_seed_lessons():
    if not SEED_FILE.exists():
        return []
    raw_list = json.loads(SEED_FILE.read_text(encoding='utf-8'))
    return [MockLesson(item) for item in raw_list]


MOCK_LESSONS = _load_seed_lessons()
MOCK_LESSONS_BY_PK = {l.pk: l for l in MOCK_LESSONS}


def get_mock_lessons(subject=None, grade=None):
    items = list(MOCK_LESSONS)
    if subject:
        items = [l for l in items if l.subject == subject]
    if grade and grade in ('m4', 'm5', 'm6'):
        items = [l for l in items if l.grade == grade]
    return items


def get_mock_lesson(pk):
    return MOCK_LESSONS_BY_PK.get(int(pk))


# 📌 ข้อมูลจำลองสำหรับห้องเรียน (Classrooms, Videos, Files, Quizzes)
class MockClassroomVideo:
    def __init__(self, pk, classroom, title, youtube_url):
        self.pk = pk
        self.id = pk
        self.classroom = classroom
        self.title = title
        self.youtube_url = youtube_url
        self.video_file = None
        self.added_by = MOCK_TEACHER
        self.created_at = datetime(2026, 9, 15, 10, 30)

    @property
    def youtube_embed_url(self):
        return "https://www.youtube.com/embed/URUJD5NEXC8"


class MockFileField:
    def __init__(self, url, name):
        self.url = url
        self.name = name


class MockClassroomFile:
    def __init__(self, pk, classroom, title, filename):
        self.pk = pk
        self.id = pk
        self.classroom = classroom
        self.title = title
        self.file = MockFileField(url="#mockup-file", name=filename)
        self.added_by = MOCK_TEACHER
        self.uploaded_at = datetime(2026, 9, 16, 14, 0)

    @property
    def filename(self):
        return self.file.name


class MockClassroomQuizAttempt:
    def __init__(self, pk, quiz, user, student_name, student_class, student_number, score, max_score):
        self.pk = pk
        self.id = pk
        self.quiz = quiz
        self.user = user
        self.student_name = student_name
        self.student_class = student_class
        self.student_number = student_number
        self.score = score
        self.max_score = max_score
        self.started_at = datetime(2026, 9, 20, 9, 0)
        self.submitted_at = datetime(2026, 9, 20, 9, 15)
        self.answers = MockListManager([])

    @property
    def percent(self):
        return round(self.score / self.max_score * 100, 1) if self.max_score else 0


class MockClassroomQuiz:
    def __init__(self, pk, classroom, title, questions):
        self.pk = pk
        self.id = pk
        self.classroom = classroom
        self.title = title
        self.created_by = MOCK_TEACHER
        self.created_at = datetime(2026, 9, 18, 11, 0)
        self.questions = MockListManager(questions)
        self.my_attempt = None
        self.attempts = MockListManager([
            MockClassroomQuizAttempt(1, self, MOCK_STUDENT, "สมชาย สายวิทย์", "ม.4/1", "15", 4, 5),
            MockClassroomQuizAttempt(2, self, MOCK_STUDENT_2, "กมลชนก รักชีวะ", "ม.4/1", "8", 5, 5),
            MockClassroomQuizAttempt(3, self, MOCK_STUDENT_3, "ธนภัทร เก่งวิทย์", "ม.4/2", "21", 3, 5),
        ])

    @property
    def question_count(self):
        return len(self.questions)


class MockClassroom:
    def __init__(self, pk, code, name, teacher, students):
        self.pk = pk
        self.id = pk
        self.code = code
        self.name = name
        self.teacher = teacher
        self.students = MockListManager(students)
        self.created_at = datetime(2026, 9, 1, 8, 30)
        self.videos = MockListManager([])
        self.files = MockListManager([])
        self.quizzes = MockListManager([])


def _build_mock_classrooms():
    sample_questions = []
    for l in MOCK_LESSONS:
        if l.subject == 'bio' and len(l.questions) > 0:
            sample_questions.extend(l.questions.all()[:5])
            break

    room1 = MockClassroom(
        pk=1,
        code="BIO101",
        name="ชีววิทยา ม.4 ภาคเรียนที่ 1 (โครงสร้างเซลล์)",
        teacher=MOCK_TEACHER,
        students=[MOCK_STUDENT, MOCK_STUDENT_2, MOCK_STUDENT_3],
    )
    room1.videos = MockListManager([
        MockClassroomVideo(1, room1, "สรุปโครงสร้างและหน้าที่ของออร์แกเนลล์ในเซลล์ (3D Animation)", "https://www.youtube.com/watch?v=URUJD5NEXC8"),
        MockClassroomVideo(2, room1, "การลำเลียงสารผ่านเข้า-ออกเซลล์ และออสโมซิส", "https://www.youtube.com/watch?v=URUJD5NEXC8"),
    ])
    room1.files = MockListManager([
        MockClassroomFile(1, room1, "ใบสรุปความรู้ บทที่ 1 การศึกษาชีววิทยา (PDF)", "bio_ch1_summary.pdf"),
        MockClassroomFile(2, room1, "ตารางเปรียบเทียบเซลล์พืชและเซลล์สัตว์", "plant_vs_animal_cell.pdf"),
    ])
    room1.quizzes = MockListManager([
        MockClassroomQuiz(1, room1, "แบบทดสอบเก็บคะแนนครั้งที่ 1: ธรรมชาติของสิ่งมีชีวิต", sample_questions),
    ])

    room2 = MockClassroom(
        pk=2,
        code="ALV690",
        name="ติวเข้มชีววิทยา ม.ปลาย & เก็งข้อสอบ A-Level",
        teacher=MOCK_TEACHER,
        students=[MOCK_STUDENT, MOCK_STUDENT_2],
    )
    room2.videos = MockListManager([
        MockClassroomVideo(3, room2, "เทคนิควิเคราะห์โจทย์การแบ่งเซลล์ Mitosis vs Meiosis", "https://www.youtube.com/watch?v=URUJD5NEXC8"),
    ])
    room2.files = MockListManager([
        MockClassroomFile(3, room2, "รวมข้อสอบเก่าชีววิทยา A-Level พร้อมเฉลยละเอียด", "alevel_bio_practice.pdf"),
    ])
    room2.quizzes = MockListManager([
        MockClassroomQuiz(2, room2, "พรีเทสต์: การแบ่งเซลล์และพันธุศาสตร์", sample_questions),
    ])
    return [room1, room2]


MOCK_CLASSROOMS = _build_mock_classrooms()


def get_mock_classroom(code):
    for room in MOCK_CLASSROOMS:
        if room.code.upper() == (code or "").upper():
            return room
    return MOCK_CLASSROOMS[0] if MOCK_CLASSROOMS else None


# 📌 ชุดการ์ดคำศัพท์จำลอง (Mock Flashcard Decks)
class MockFlashcard:
    def __init__(self, pk, deck, front, back, order=1):
        self.pk = pk
        self.id = pk
        self.deck = deck
        self.front = front
        self.back = back
        self.order = order
        self.created_at = datetime(2026, 9, 10, 12, 0)


class MockFlashcardDeck:
    def __init__(self, pk, title, cards_data):
        self.pk = pk
        self.id = pk
        self.owner = MOCK_STUDENT
        self.title = title
        self.created_at = datetime(2026, 9, 10, 12, 0)
        self.cards = MockListManager([
            MockFlashcard(idx, self, c['front'], c['back'], idx)
            for idx, c in enumerate(cards_data, start=1)
        ])

    @property
    def card_count(self):
        return len(self.cards)


MOCK_FLASHCARD_DECKS = [
    MockFlashcardDeck(1, "ศัพท์ออร์แกเนลล์ภายในเซลล์ (ออกสอบบ่อย)", [
        {"front": "Mitochondria (ไมโทคอนเดรีย)", "back": "แหล่งสร้างพลังงาน ATP ของเซลล์ (เยื่อหุ้ม 2 ชั้น)"},
        {"front": "Chloroplast (คลอโรพลาสต์)", "back": "ออร์แกเนลล์ที่ทำหน้าที่สังเคราะห์ด้วยแสงในพืชและสาหร่าย (เยื่อหุ้ม 2 ชั้น)"},
        {"front": "Ribosome (ไรโบโซม)", "back": "ทำหน้าที่สังเคราะห์โปรตีน (ไม่มีเยื่อหุ้ม)"},
        {"front": "Lysosome (ไลโซโซม)", "back": "ถุงบรรจุเอนไซม์ย่อยสลายสิ่งแปลกปลอม พบเฉพาะในเซลล์สัตว์"},
    ]),
    MockFlashcardDeck(2, "ระยะการแบ่งเซลล์ (Mitosis & Meiosis)", [
        {"front": "Prophase I (โพรเฟส I)", "back": "โครโมโซมคู่เหมือนมาเข้าคู่กัน (Synapsis) และเกิด Crossing over"},
        {"front": "Metaphase (เมทาเฟส)", "back": "โครโมโซมเรียงตัวกันบริเวณแนวกึ่งกลางเซลล์ (Metaphase plate)"},
        {"front": "Anaphase (แอนาเฟส)", "back": "ซิสเตอร์โครมาทิด (หรือโฮโมโลกัสโครโมโซมใน Anaphase I) แยกออกจากกันไปยังขั้วเซลล์"},
    ]),
]


# 📌 ประวัติการทำแบบฝึกหัด/ข้อสอบจำลอง (Mock Attempts)
class MockAttemptAnswer:
    def __init__(self, pk, order, question, selected_choice=None, text_answer="", is_correct=True, points_earned=1.0):
        self.pk = pk
        self.id = pk
        self.order = order
        self.question = question
        self.selected_choice = selected_choice
        self.text_answer = text_answer
        self.is_correct = is_correct
        self.points_earned = points_earned


class MockAttempt:
    def __init__(self, pk, mode, lesson, grade="m4", chapter=1, score=8.0, max_score=10.0, answers=None):
        self.pk = pk
        self.id = pk
        self.user = MOCK_STUDENT
        self.mode = mode
        self.lesson = lesson
        self.grade = grade
        self.chapter = chapter
        self.score = score
        self.max_score = max_score
        self.started_at = datetime(2026, 9, 22, 15, 0)
        self.submitted_at = datetime(2026, 9, 22, 15, 12)
        self.answers = MockListManager(answers or [])

    def get_mode_display(self):
        return "ข้อสอบ" if self.mode == "exam" else "แบบฝึกหัด"

    def get_grade_display(self):
        return GRADE_DISPLAY.get(self.grade, self.grade)

    @property
    def percent(self):
        return round(self.score / self.max_score * 100, 1) if self.max_score else 0


def _build_default_attempts():
    bio_lesson = next((l for l in MOCK_LESSONS if l.subject == 'bio' and len(l.questions) > 0), None)
    if not bio_lesson:
        return {}
    ans_list = []
    for idx, q in enumerate(bio_lesson.questions.all()[:5], start=1):
        correct_choice = next((c for c in q.choices.all() if c.is_correct), q.choices.first())
        ans_list.append(MockAttemptAnswer(idx, idx, q, selected_choice=correct_choice, is_correct=True, points_earned=q.points))

    att1 = MockAttempt(1, 'practice', bio_lesson, grade=bio_lesson.grade, chapter=bio_lesson.chapter, score=5.0, max_score=5.0, answers=ans_list)
    att2 = MockAttempt(2, 'exam', bio_lesson, grade=bio_lesson.grade, chapter=bio_lesson.chapter, score=4.0, max_score=5.0, answers=ans_list)
    return {1: att1, 2: att2}


MOCK_ATTEMPTS = _build_default_attempts()


# 📌 ห้องสนทนาติวเตอร์ AI ชีววิทยาจำลองในหน่วยความจำ (Mock BioChat Sessions)
class MockBioChatMessage:
    def __init__(self, role, content, sources=None, engine="local_bio_rag"):
        self.role = role
        self.content = content
        self.sources = sources or []
        self.engine = engine
        self.created_at = datetime.now()

    def get_role_display(self):
        return "ผู้เรียน/ผู้ถาม" if self.role == 'user' else "ติวเตอร์ AI ชีววิทยา"


class MockBioChatSession:
    def __init__(self, pk, title, lesson=None, tutor_mode='explain', messages=None):
        self.pk = pk
        self.id = pk
        self.user = MOCK_STUDENT
        self.title = title
        self.lesson = lesson
        self.tutor_mode = tutor_mode
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.messages = MockListManager(messages or [])

    def get_tutor_mode_display(self):
        return TUTOR_MODE_DISPLAY.get(self.tutor_mode, self.tutor_mode)


MOCK_CHAT_SESSIONS = [
    MockBioChatSession(
        pk=1,
        title="เปรียบเทียบเซลล์พืชกับเซลล์สัตว์",
        lesson=MOCK_LESSONS[0] if MOCK_LESSONS else None,
        tutor_mode='explain',
        messages=[
            MockBioChatMessage('user', 'เซลล์พืชกับเซลล์สัตว์ต่างกันอย่างไร?'),
            MockBioChatMessage(
                'assistant',
                '📖 **อธิบายความรู้ชีววิทยา: โครงสร้างและหน้าที่ของเซลล์**\n\n'
                'ความแตกต่างหลักระหว่างเซลล์พืชและเซลล์สัตว์ ได้แก่:\n'
                '• **เซลล์พืช**: มีผนังเซลล์ (Cell wall จากเซลลูโลส), มีคลอโรพลาสต์ (Chloroplast) สำหรับสังเคราะห์ด้วยแสง และมีแวคิวโอลกลางขนาดใหญ่ (Central vacuole) แต่ไม่มีเซนทริโอลและไลโซโซม\n'
                '• **เซลล์สัตว์**: ไม่มีผนังเซลล์และไม่มีคลอโรพลาสต์ แต่มีเซนทริโอล (Centriole) ช่วยในการแบ่งเซลล์ และมีไลโซโซม (Lysosome) ช่วยย่อยสลายสิ่งแปลกปลอม\n\n'
                '💡 **เกร็ดความรู้เสริม:** จำเยื่อหุ้มออร์แกเนลล์: "ไร้เยื่อ = ไร-เซน-ไซ (ไรโบโซม เซนทริโอล ไซโทสเกเลตัน)" / "สองชั้น = นิว-ไม-คลอ (นิวเคลียส ไมโทคอนเดรีย คลอโรพลาสต์)"',
                sources=[
                    {
                        'type': 'curriculum',
                        'id': 'bio-core-cell',
                        'title': 'โครงสร้างและหน้าที่ของเซลล์ (Cell Structure & Organelles)',
                        'badge': 'หลักสูตรชีววิทยา ม.4',
                        'snippet': 'เซลล์พืชมีผนังเซลล์ คลอโรพลาสต์ และแวคิวโอลขนาดใหญ่ ส่วนเซลล์สัตว์ไม่มีผนังเซลล์และไม่มีคลอโรพลาสต์ แต่มีเซนทริโอลและไลโซโซม…',
                        'score_percent': 95,
                    }
                ],
                engine='local_bio_rag',
            ),
        ],
    ),
]
