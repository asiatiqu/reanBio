from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from reanBio import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('lessons/', views.lessons_view, name='lessons'),
    path('profile/', views.profile, name='profile'),
    path('classrooms/', views.my_classroom_view, name='my_classrooms'),
    path('classrooms/join/', views.join_classroom_view, name='join_classroom'),
    path('classrooms/<str:code>/', views.classroom_detail_view, name='classroom_detail'),
    path('classrooms/<str:code>/videos/add/', views.classroom_add_video_view, name='classroom_add_video'),
    path('classrooms/<str:code>/files/add/', views.classroom_add_file_view, name='classroom_add_file'),
    path('classrooms/<str:code>/quizzes/add/', views.classroom_add_quiz_view, name='classroom_add_quiz'),
    path('classroom-quizzes/<int:quiz_pk>/start/', views.classroom_quiz_start_view, name='classroom_quiz_start'),
    path('classroom-quiz-attempts/<int:attempt_pk>/', views.classroom_quiz_take_view, name='classroom_quiz_take'),
    path('classroom-quiz-attempts/<int:attempt_pk>/result/', views.classroom_quiz_result_view, name='classroom_quiz_result'),
    path('teacher/dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('lessons/', views.lessons_view, name='lessons'),
    path('lessons/<int:pk>/', views.lesson_detail_view, name='lesson_detail'),
    path('flashcards/', views.flashcards_view, name='flashcards'),
    path('quiz-generator/', views.quiz_generator_view, name='quiz_generator'),
    path('quiz-generator/start/', views.start_generated_quiz, name='start_generated_quiz'),

    # 📌 ระบบแบบฝึกหัด / ข้อสอบ (แดชบอร์ดรวมอยู่ในหน้าโปรไฟล์)
    path('lessons/<int:pk>/exercise/', views.lesson_exercise_view, name='lesson_exercise'),
    path('lessons/<int:pk>/exercise/start/', views.start_practice_attempt, name='start_practice_attempt'),
    path('lessons/<int:pk>/exercise/pdf/', views.exercise_pdf_view, name='exercise_pdf'),
    path('lessons/<int:pk>/exam/start/', views.start_lesson_exam, name='start_lesson_exam'),
    path('attempts/<int:attempt_pk>/', views.attempt_take_view, name='attempt_take'),
    path('attempts/<int:attempt_pk>/result/', views.attempt_result_view, name='attempt_result'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
