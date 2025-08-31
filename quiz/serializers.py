from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Quiz, Question, Answer, QuizAttempt, UserResponse


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'order']

class AnswerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'is_correct', 'order']

class QuizSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'time_limit', 'questions_count', 'created_at']
    
    def get_questions_count(self, obj):
        return obj.questions.count()
    
    def validate_time_limit(self, value):
        if value and value < 1:
            raise serializers.ValidationError("Time limit must be at least 1 minute")
        return value

class QuestionSerializer(serializers.ModelSerializer):
    answers = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'points', 'answers']

class QuestionCreateSerializer(serializers.ModelSerializer):
    answers = AnswerCreateSerializer(many=True, write_only=True)

    class Meta:
         model = Question
         fields = ['id', 'question_text', 'question_type', 'points', 'order', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = Question.objects.create(**validated_data)

        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)

        return question
    
    def validate_answers(self, answers):
        if not answers:
            raise serializers.ValidationError("Questions must have at least one answer")
        if len(answers) < 2:
            raise serializers.ValidationError("Multiple choice questions need at least 2 answers")
        
        correct_answers = [answer for answer in answers if answer.get('is_correct')]
        if len(correct_answers) != 1:
            raise serializers.ValidationError("Questions must have exactly one correct answer")
        
        return answers
    
class QuizListSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    total_questions = serializers.ReadOnlyField()
    total_points = serializers.ReadOnlyField()

    class Meta:
         model = Quiz
         fields = ['id', 'title', 'description', 'creator', 'total_questions', 'total_points', 'time_limit', 'created_at', 'is_active']


class QuizDetailSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    total_questions = serializers.ReadOnlyField()
    total_points = serializers.ReadOnlyField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'creator', 'questions', 'total_questions', 'total_points','time_limit', 'max_attempts', 'created_at','updated_at', 'is_active']

class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'max_attempts']
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)
    
class UserResponseSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    selected_answer = AnswerSerializer(read_only=True)

    class Meta:
        model = UserResponse
        fields = ['id', 'question', 'selected_answer', 'text_answer', 'is_correct', 'answered_at']


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer_id = serializers.IntegerField(required=False)
    text_answer = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')
        text_answer = data.get('text_answer')

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            raise serializers.ValidationError("Question does not exist")
        if question.question_type in ['MC', 'TF']:
            if not answer_id:
                raise serializers.ValidationError("Answer ID is required for multiple choice questions")
            try:
                answer = Answer.objects.get(id=answer_id, question=question)
                data['answer'] = answer
            except Answer.DoesNotExist:
                raise serializers.ValidationError("Invalid answer for this question")
        
        elif question.question_type == 'SA':
            if not text_answer:
                raise serializers.ValidationError("Text answer is required for short answer questions")
        
        data['question'] = question
        return data
class QuizAttemptSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    quiz = QuizListSerializer(read_only=True)
    responses = UserResponseSerializer(many=True, read_only=True)
    percentage_score = serializers.ReadOnlyField()

    class Meta:
        model = QuizAttempt
        fields = ['id', 'user', 'quiz', 'started_at', 'completed_at','score', 'total_points', 'percentage_score', 'responses']
        

    


    