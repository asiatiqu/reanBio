from django.contrib import admin, messages
from .models import Lesson, Question, Choice, Attempt, AttemptAnswer, AIFeedback, KnowledgeDocument
from .ai_helper import extract_pdf_text, AskAIError


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


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    # 📌 อัปโหลดไฟล์ PDF เนื้อหาชีวะเพิ่มเติมที่นี่ — ระบบจะแกะข้อความออกมาอัตโนมัติให้ทันที
    # แล้วฟีเจอร์ "ถาม AI" จะค้นหาเนื้อหาจากที่นี่มาแนบตอบด้วย (ไม่ผูกกับบทเรียนไหนเป็นพิเศษ)
    list_display = ('title', 'uploaded_by', 'uploaded_at', 'extracted_text_status')
    fields = ('title', 'file', 'extracted_text', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('extracted_text', 'uploaded_by', 'uploaded_at')
    search_fields = ('title',)

    def extracted_text_status(self, obj):
        if not obj.extracted_text:
            return "⚠️ ยังไม่มีข้อความ (อาจเป็น PDF สแกนภาพ)"
        return f"✅ แกะได้ {len(obj.extracted_text):,} ตัวอักษร"
    extracted_text_status.short_description = "สถานะการแกะข้อความ"

    def save_model(self, request, obj, form, change):
        is_new_file = 'file' in form.changed_data
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

        if is_new_file:
            try:
                obj.extracted_text = extract_pdf_text(obj.file.path)
                obj.save(update_fields=['extracted_text'])
                if not obj.extracted_text:
                    self.message_user(
                        request,
                        "อัปโหลดไฟล์สำเร็จ แต่แกะข้อความไม่ได้เลย — ไฟล์นี้อาจเป็น PDF ที่สแกนมาเป็นรูปภาพ ไม่มีเลเยอร์ข้อความให้อ่าน "
                        "(AI จะยังไม่ใช้เอกสารนี้ประกอบการตอบจนกว่าจะมีข้อความ)",
                        level=messages.WARNING,
                    )
            except AskAIError as exc:
                self.message_user(request, f"แกะข้อความจากไฟล์ไม่สำเร็จ: {exc}", level=messages.ERROR)


admin.site.register(Lesson)
admin.site.register(AttemptAnswer)
