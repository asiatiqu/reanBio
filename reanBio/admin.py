from django.contrib import admin
from .models import Lesson, Question, Choice, Attempt, AttemptAnswer


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


admin.site.register(Lesson)
admin.site.register(AttemptAnswer)
