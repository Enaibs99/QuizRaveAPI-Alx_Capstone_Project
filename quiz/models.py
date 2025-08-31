from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Quiz(models.Model):
    #When a complete quiz is created by a user
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit in minutes")
    max_attempts = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title
    
    @property
    def total_questions(self):
        return self.questions.count()
    
    @property
    def total_points(self):
        return self.questions.aggregate( total=models.Sum('points'))['total'] or 0



class Question(models.Model):
    QUESTION_TYPES = [
        ('MC', 'Multiple Choice'),
        ('TF', 'True/False'),
        ('SA', 'Short Answer'),

    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES, default='MC')
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']
        unique_together = ['quiz', 'order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order} {self.question_text[:50]}..."
    
    def save(self, *args, **kwargs):
        if not self.order:
            last_question = self.quiz.questions.order_by('order').last()
            self.order = (last_question.order + 1) if last_question else 1
        super().save(*args, **kwargs)
    
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.question} - {self.answer_text[:30]}{'...' if len(self.answer_text) > 30 else ''}"

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(null=True, blank=True)
    total_points = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        status = "Completed" if self.completed_at else "In Progress"
        return f"{self.user.username} - {self.quiz.title} ({status})"
    
    @property
    def is_completed(self):
        return self.completed_at is not None
    
    @property
    def percentage_score(self):
        if self.score is not None and self.total_points:
            return round((self.score / self.total_points) * 100, 2)
        return 0

    
class UserResponse(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)
    text_answer = models.TextField(blank=True)  # For short answer questions
    is_correct = models.BooleanField(null=True)  # Calculated field

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.user.username} - {self.question}"
    
    def save(self, *args, **kwargs):
        # Automatically calculate if answer is correct
        if self.question.question_type in ['MC', 'TF'] and self.selected_answer:
            self.is_correct = self.selected_answer.is_correct
        super().save(*args, **kwargs)
    




