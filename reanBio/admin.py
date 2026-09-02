from django.contrib import admin
from .models import Lesson, Question, Choice, Attempt, AttemptAnswer, AIFeedback


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'order', 'question_type', 'text', 'points')
    list_filter = ('lesson__grade', 'lesson__chapter', 'question_type')
    search_fields = ('text',)
    inlines = [ChoiceInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'mode', 'lesson', 'grade', 'chapter', 'score', 'max_score', 'submitted_at')
    list_filter = ('mode', 'grade', 'chapter')


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    # 📌 ใช้ดูว่าคำตอบของฟีเจอร์ "ถาม AI" ช่วยผู้ใช้ได้จริงไหม (👍/👎) เพื่อเอาไปปรับปรุง system prompt/เนื้อหาต่อ
    list_display = ('user', 'is_helpful', 'lesson', 'created_at')
    list_filter = ('is_helpful', 'lesson')
    search_fields = ('question', 'answer', 'user__username')
    readonly_fields = ('user', 'question', 'answer', 'lesson', 'is_helpful', 'created_at')


admin.site.register(Lesson)
admin.site.register(AttemptAnswer)
