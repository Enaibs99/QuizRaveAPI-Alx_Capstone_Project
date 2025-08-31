from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Quiz, Question, Answer, QuizAttempt, UserResponse
from .serializers import  (QuizListSerializer, QuizDetailSerializer, QuizCreateSerializer,QuestionSerializer, QuestionCreateSerializer,QuizAttemptSerializer, SubmitAnswerSerializer, UserSerializer)
from .permissions import IsCreatorOrReadOnly, CanTakeQuiz, IsAttemptOwner


def home(request):
    return HttpResponse("Welcome to QuizRave API")


# Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not all([username, email, password]):
        return Response({'error': 'Username, email, and password are required'},status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, {'error': 'Username already exists'},)
    
    user = User.objects.create_user(username=username, email=email, password=password)
    token, created = Token.objects.get_or_create(user=user)

    return Response({'token': token.key,'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key,'user': UserSerializer(user).data})
    
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout(request):
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out'})
    except:
        return Response({'error': 'Error logging out'}, status=status.HTTP_400_BAD_REQUEST)
    
# Quiz Views
class QuizListCreateView(generics.ListCreateAPIView):
    queryset = Quiz.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuizCreateSerializer
        return QuizListSerializer

class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreatorOrReadOnly]

class MyQuizzesView(generics.ListAPIView):
    serializer_class = QuizListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Quiz.objects.filter(creator=self.request.user)
    
# Question Views
class QuestionCreateView(generics.CreateAPIView):
    serializer_class = QuestionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        quiz = get_object_or_404(Quiz, id=self.kwargs['quiz_id'])

        # Check if user is the quiz creator
        if quiz.creator != self.request.user:
            return Response( {'error': 'You can only add questions to your own quizzes'},status=status.HTTP_403_FORBIDDEN)
        
        serializer.save(quiz=quiz)

# Quiz Attempt Views
@api_view(['POST'])
def start_quiz_attempt(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if user has incomplete attempts
    incomplete_attempt = QuizAttempt.objects.filter(
        user=request.user, 
        quiz=quiz, 
        completed_at__isnull=True
    ).first()
    
    if incomplete_attempt:
        return Response({'error': 'You have an incomplete attempt for this quiz'}, status=status.HTTP_400_BAD_REQUEST)
    # Check attempt limits
    completed_attempts = QuizAttempt.objects.filter(user=request.user,quiz=quiz,completed_at__isnull=False).count()
    if completed_attempts >= quiz.max_attempts:
        return Response({'error': 'You have exceeded the maximum attempts for this quiz'},status=status.HTTP_400_BAD_REQUEST)
    
    # Create new attempt
    attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz)
    
    return Response({'attempt_id': attempt.id,'quiz': QuizDetailSerializer(quiz).data,'started_at': attempt.started_at}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def submit_answer(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    if attempt.completed_at:
        return Response({'error': 'This quiz attempt is already completed'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = SubmitAnswerSerializer(data=request.data)
    if serializer.is_valid():
        question = serializer.validated_data['question']
        # Ensure question belongs to the quiz
        if question.quiz != attempt.quiz:
            return Response({'error': 'Question does not belong to this quiz'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update response
        response_data = {'attempt': attempt,'question': question}

        if question.question_type in ['MC', 'TF']:
            response_data['selected_answer'] = serializer.validated_data['answer']
        else:
            response_data['text_answer'] = serializer.validated_data['text_answer']
        
        user_response, created = UserResponse.objects.update_or_create(attempt=attempt,question=question,defaults=response_data)

        return Response({'message': 'Answer submitted successfully','response_id': user_response.id}, status=status.HTTP_201_CREATED)
    
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def complete_quiz_attempt(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    if attempt.completed_at:
        return Response({'error': 'This quiz attempt is already completed'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate score
    total_points = 0
    earned_points = 0
    
    for question in attempt.quiz.questions.all():
        total_points += question.points


        try:
            response = UserResponse.objects.get(attempt=attempt, question=question)
            if response.is_correct:
                earned_points += question.points
        except UserResponse.DoesNotExist:
            # Question not answered
            pass

        # Update attempt
    attempt.completed_at = timezone.now()
    attempt.score = earned_points
    attempt.total_points = total_points
    attempt.save()

    return Response({'message': 'Quiz completed successfully','score': earned_points,'total_points': total_points,'percentage': attempt.percentage_score,'completed_at': attempt.completed_at})

class QuizAttemptDetailView(generics.RetrieveAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated, IsAttemptOwner]
    
    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)
    
class MyAttemptsView(generics.ListAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)

    
    




