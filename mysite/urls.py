from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from reanBio import views

urlpatterns = [
    path('', views.home, name='home'),
    path('ask-ai/', views.ask_ai_view, name='ask_ai'),
    path('ask-ai/new/', views.bio_tutor_new_session_view, name='ask_ai_new'),
    path('ask-ai/sessions/<int:session_pk>/', views.ask_ai_view, name='ask_ai_session'),
    path('ask-ai/sessions/<int:session_pk>/delete/', views.bio_tutor_delete_session_view, name='ask_ai_delete_session'),
    path('ai/feedback/', views.ai_feedback_view, name='ai_feedback'),

    # 📌 โหมด Mockup: ปุ่มสลับบทบาท นักเรียน / คุณครู / ผู้เยี่ยมชม (ไม่ต้องสมัครสมาชิกจริง)
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('password-reset/', views.login_view, name='password_reset'),
    path('student-info/', views.student_info_view, name='student_info'),

    path('lessons/', views.lessons_view, name='lessons'),
    path('lessons/<int:pk>/', views.lesson_detail_view, name='lesson_detail'),
    path('profile/', views.profile, name='profile'),

    path('classrooms/', views.my_classroom_view, name='my_classrooms'),
    path('classrooms/join/', views.join_classroom_view, name='join_classroom'),
    path('classrooms/<str:code>/', views.classroom_detail_view, name='classroom_detail'),
    path('classrooms/<str:code>/edit/', views.classroom_edit_view, name='classroom_edit'),
    path('classrooms/<str:code>/delete/', views.classroom_delete_view, name='classroom_delete'),
    path('classrooms/<str:code>/students/', views.classroom_students_view, name='classroom_students'),
    path('classrooms/<str:code>/students/<int:student_pk>/remove/', views.classroom_remove_student_view, name='classroom_remove_student'),
    path('classrooms/<str:code>/students/export/', views.classroom_students_export_view, name='classroom_students_export'),
    path('classrooms/<str:code>/videos/<int:video_pk>/', views.classroom_video_watch_view, name='classroom_video_watch'),
    path('classrooms/<str:code>/videos/add/', views.classroom_add_video_view, name='classroom_add_video'),
    path('classrooms/<str:code>/files/add/', views.classroom_add_file_view, name='classroom_add_file'),
    path('classrooms/<str:code>/quizzes/add/', views.classroom_add_quiz_view, name='classroom_add_quiz'),
    path('classroom-quizzes/<int:quiz_pk>/start/', views.classroom_quiz_start_view, name='classroom_quiz_start'),
    path('classroom-quiz-attempts/<int:attempt_pk>/', views.classroom_quiz_take_view, name='classroom_quiz_take'),
    path('classroom-quiz-attempts/<int:attempt_pk>/result/', views.classroom_quiz_result_view, name='classroom_quiz_result'),
    path('classroom-quizzes/<int:quiz_pk>/attempts/', views.classroom_quiz_attempts_view, name='classroom_quiz_attempts'),
    path('classroom-quizzes/<int:quiz_pk>/attempts/export/', views.classroom_quiz_export_view, name='classroom_quiz_export'),
    path('teacher/dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),

    path('flashcards/', views.flashcards_view, name='flashcards'),
    path('quiz-generator/', views.quiz_generator_view, name='quiz_generator'),
    path('quiz-generator/start/', views.start_generated_quiz, name='start_generated_quiz'),

    path('my-flashcards/', views.my_flashcards_view, name='my_flashcards'),
    path('my-flashcards/<int:deck_pk>/', views.flashcard_deck_detail_view, name='flashcard_deck_detail'),
    path('my-flashcards/<int:deck_pk>/delete/', views.flashcard_deck_delete_view, name='flashcard_deck_delete'),
    path('my-flashcards/<int:deck_pk>/study/', views.flashcard_deck_study_view, name='flashcard_deck_study'),
    path('my-flashcards/cards/<int:card_pk>/delete/', views.flashcard_card_delete_view, name='flashcard_card_delete'),

    path('lessons/<int:pk>/exercise/', views.lesson_exercise_view, name='lesson_exercise'),
    path('lessons/<int:pk>/exercise/start/', views.start_practice_attempt, name='start_practice_attempt'),
    path('lessons/<int:pk>/exercise/pdf/', views.exercise_pdf_view, name='exercise_pdf'),
    path('lessons/<int:pk>/exam/start/', views.start_lesson_exam, name='start_lesson_exam'),
    path('attempts/<int:attempt_pk>/', views.attempt_take_view, name='attempt_take'),
    path('attempts/<int:attempt_pk>/result/', views.attempt_result_view, name='attempt_result'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
