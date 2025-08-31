from django.urls import path 
from . import views

urlpatterns = [
    # Authentication URLs
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),

    # Quiz URLs
    path('quizzes/', views.QuizListCreateView.as_view(), name='quiz-list-create'),
    path('quizzes/<int:pk>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/my-quizzes/', views.MyQuizzesView.as_view(), name='my-quizzes'),
    
    # Question URLs
    path('quizzes/<int:quiz_id>/questions/', views.QuestionCreateView.as_view(), name='question-create'),

    # Quiz Attempt URLs
    path('quizzes/<int:quiz_id>/start/', views.start_quiz_attempt, name='start-quiz'),
    path('attempts/<int:attempt_id>/submit-answer/', views.submit_answer, name='submit-answer'),
    path('attempts/<int:attempt_id>/complete/', views.complete_quiz_attempt, name='complete-quiz'),
    path('attempts/<int:pk>/', views.QuizAttemptDetailView.as_view(), name='attempt-detail'),
    path('my-attempts/', views.MyAttemptsView.as_view(), name='my-attempts'),

]