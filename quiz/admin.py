from django.contrib import admin
from .models import Quiz, Question, Answer, QuizAttempt, UserResponse

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
     list_display = ['title', 'creator', 'total_questions', 'total_points', 'is_active', 'created_at']
     list_filter = ['is_active', 'created_at', 'creator']
     search_fields = ['title', 'description']
     readonly_fields = ['created_at', 'updated_at']

class AnswerInline(admin.TabularInline):
     model = Answer
     extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'quiz']
    inlines = [AnswerInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer_text', 'is_correct']
    list_filter = ['is_correct', 'question__quiz']

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'total_points', 'percentage_score', 'started_at', 'is_completed']
    list_filter = ['completed_at', 'quiz']
    readonly_fields = ['started_at', 'percentage_score']

@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_answer', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'question__question_type']
    readonly_fields = ['answered_at']