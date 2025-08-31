from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from .models import Quiz, Question, Answer, QuizAttempt, UserAnswer


class QuizAPITestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1',email='test1@example.com',password='testpass123')
        self.user2 = User.objects.create_user(username='testuser2',email='test2@example.com',password='testpass123')
        
        # Create test quiz with questions
        self.quiz = Quiz.objects.create(title='Test Quiz',description='A test quiz',created_by=self.user1,time_limit=30,max_attempts=3)

        # Create questions
        self.question1 = Question.objects.create(quiz=self.quiz,text='What is 2 + 2?',question_type='single_choice',points=10, order=1)
        self.question2 = Question.objects.create( quiz=self.quiz,text='Which are programming languages?', question_type='multiple_choice', points=15,order=2)

        # Create answers
        Answer.objects.create(question=self.question1,text='3',is_correct=False)
        Answer.objects.create(question=self.question1,text='4',is_correct=True,explanation= '2 + 2 equals 4')
        Answer.objects.create(question=self.question2,text='Python',is_correct=True)
        Answer.objects.create(question=self.question2,text='JavaScript',is_correct=True)
        Answer.objects.create(question=self.question2,text='HTML',is_correct=False,explanation='HTML is a markup language, not a programming language')

    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate(self, user):
        token = self.get_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

class QuizListCreateTests(QuizAPITestCase):
    
    def test_list_quizzes_authenticated(self):
        self.authenticate(self.user1)
        url = reverse('quiz:quiz-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Quiz')

    def test_list_quizzes_unauthenticated(self):
        url = reverse('quiz:quiz-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_quiz(self):
        self.authenticate(self.user1)
        url = reverse('quiz:quiz-list-create')


        data = {

            'title': 'New Quiz',
            'description': 'A new test quiz',
            'time_limit': 45,
            'max_attempts': 2,
            'questions': [
                {
                    'text': 'Sample question?',
                    'question_type': 'single_choice',
                    'points': 10,
                    'order': 1,
                    'answers': [
                        {'text': 'Option A', 'is_correct': True},
                        {'text': 'Option B', 'is_correct': False}
                    ]
                }
            ]
        }


        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quiz.objects.count(), 2)
        self.assertEqual(Question.objects.count(), 3)  # 2 existing + 1 new
        self.assertEqual(Answer.objects.count(), 7)  # 5 existing + 2 new


    def test_search_quizzes(self):
        self.authenticate(self.user1)
        url = reverse('quiz:quiz-list-create')
        
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        response = self.client.get(url, {'search': 'NonExistent'})
        self.assertEqual(len(response.data['results']), 0)

class QuizDetailTests(QuizAPITestCase):
    
    def test_retrieve_quiz(self):
        self.authenticate(self.user1)
        url = reverse('quiz:quiz-detail', args=[self.quiz.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Quiz')
        self.assertEqual(len(response.data['questions']), 2)

    def test_update_quiz_non_owner(self):
        self.authenticate(self.user2)
        url = reverse('quiz:quiz-detail', args=[self.quiz.id])
        
        data = {'title': 'Hacked Title'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_quiz_owner(self):
        self.authenticate(self.user1)
        url = reverse('quiz:quiz-detail', args=[self.quiz.id])
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())

class QuizTakingTests(QuizAPITestCase):
    
    def test_take_quiz_flow(self):
        self.authenticate(self.user2)
        
        # 1. Get quiz for taking (without correct answers)
        take_url = reverse('quiz:quiz-take', args=[self.quiz.id])
        response = self.client.get(take_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that correct answers are hidden
        question_data = response.data['questions'][0]
        for answer in question_data['answers']:
            self.assertNotIn('is_correct', answer)

        # 2. Start quiz attempt
        attempt_url = reverse('quiz:attempt-list-create')
        attempt_data = {'quiz_id': self.quiz.id}
        response = self.client.post(attempt_url, attempt_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        attempt_id = response.data['id']
        
        # 3. Submit answers
        submit_url = reverse('quiz:quiz-submit', args=[attempt_id])
        
        # Get correct answers for submission
        correct_answer1 = Answer.objects.get(question=self.question1, is_correct=True)
        correct_answer2 = Answer.objects.get(question=self.question2, text='Python')

        submission_data = {
            'answers': [
                {
                    'question': self.question1.id,
                    'selected_answer': correct_answer1.id
                },
                {
                    'question': self.question2.id,
                    'selected_answer': correct_answer2.id
                }
            ]
        }



        response = self.client.post(submit_url, submission_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('score', response.data)
        self.assertEqual(response.data['correct_answers'], 2)
        
        # 4. Get results
        results_url = reverse('quiz:quiz-results', args=[attempt_id])
        response = self.client.get(results_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_answers', response.data)
        self.assertEqual(len(response.data['user_answers']), 2)


    def test_max_attempts_exceeded(self):
        """Test that max attempts limit is enforced"""
        self.authenticate(self.user2)
        
        # Create 3 attempts (max allowed)
        for i in range(3):
            QuizAttempt.objects.create(user=self.user2, quiz=self.quiz)
        
        # Try to create another attempt
        url = reverse('quiz:attempt-list-create')
        data = {'quiz_id': self.quiz.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Maximum attempts', str(response.data))
    
    def test_submit_quiz_twice(self):
        self.authenticate(self.user2)

        # Create and complete an attempt
        attempt = QuizAttempt.objects.create(user=self.user2,quiz=self.quiz,is_completed=True,completed_at=timezone.now())


        # Try to submit again
        url = reverse('quiz:quiz-submit', args=[attempt.id])
        data = {'answers': []}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_time_limit_exceeded(self):
        self.authenticate(self.user2)
        
        # Create attempt that started 35 minutes ago (exceeds 30 min limit)
        past_time = timezone.now() - timedelta(minutes=35)
        attempt = QuizAttempt.objects.create(user=self.user2,quiz=self.quiz,started_at=past_time)


         # Try to submit
        url = reverse('quiz:quiz-submit', args=[attempt.id])
        data = {'answers': []}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Time limit exceeded', str(response.data))


class QuizStatsTests(QuizAPITestCase):
    
    def test_quiz_stats_owner(self):
        self.authenticate(self.user1)
        
        # Create some completed attempts
        for score in [85, 92, 78, 65]:
            attempt = QuizAttempt.objects.create(user=self.user2,quiz=self.quiz,is_completed=True,score=score,completed_at=timezone.now())
        
        url = reverse('quiz:quiz-stats', args=[self.quiz.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_attempts'], 4)
        self.assertEqual(response.data['average_score'], 80.0)
        self.assertIn('score_distribution', response.data)

    def test_quiz_stats_non_owner(self):
        self.authenticate(self.user2)
        
        url = reverse('quiz:quiz-stats', args=[self.quiz.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
class UserDashboardTests(QuizAPITestCase):
   
    def test_user_dashboard(self):
        
        self.authenticate(self.user2)
        
        # Create some attempts
        attempt1 = QuizAttempt.objects.create(user=self.user2,quiz=self.quiz,is_completed=True,score=85,ompleted_at=timezone.now())
        attempt2 = QuizAttempt.objects.create( user=self.user2,quiz=self.quiz)

        url = reverse('quiz:user-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'testuser2')
        self.assertEqual(response.data['stats']['total_attempts'], 2)
        self.assertEqual(response.data['stats']['completed_quizzes'], 1)
        self.assertEqual(response.data['stats']['average_score'], 85.0)
        self.assertEqual(len(response.data['recent_attempts']), 2)


class QuizDuplicationTests(QuizAPITestCase):
    
    def test_duplicate_quiz(self):
        self.authenticate(self.user2)
        
        url = reverse('quiz:quiz-duplicate', args=[self.quiz.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quiz.objects.count(), 2)
        
        # Check that the new quiz has the same structure
        new_quiz = Quiz.objects.get(title__startswith='Copy of')
        self.assertEqual(new_quiz.questions.count(), 2)
        self.assertEqual( new_quiz.questions.first().answers.count(),self.question1.answers.count())

        self.assertFalse(new_quiz.is_active)  # Should start inactive

class ValidationTests(QuizAPITestCase):
    
    def test_invalid_answer_question_mismatch(self):
        self.authenticate(self.user2)
        
        # Create another quiz
        other_quiz = Quiz.objects.create(title='Other Quiz',created_by=self.user1)
        other_question = Question.objects.create(quiz=other_quiz,text='Other question?', question_type='single_choice',points=5, order=1)
        other_answer = Answer.objects.create(question=other_question,text='Other answer',is_correct=True)

        # Start attempt on original quiz
        attempt = QuizAttempt.objects.create(user=self.user2, quiz=self.quiz)

        # Try to submit answer from different quiz
        url = reverse('quiz:quiz-submit', args=[attempt.id])
        data = {
            'answers': [
                {
                    'question': self.question1.id,
                    'selected_answer': other_answer.id  # Wrong quiz!
                }
            ]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_quiz_without_questions(self):
        self.authenticate(self.user1)
        url = reverse('quiz:quiz-list-create')

        data = {
            'title': 'Empty Quiz',
            'description': 'A quiz with no questions'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        quiz = Quiz.objects.get(title='Empty Quiz')
        self.assertEqual(quiz.questions.count(), 0)


class PermissionTests(QuizAPITestCase):
    
    def test_view_own_attempts_only(self):
        # Create attempts for both users
        attempt1 = QuizAttempt.objects.create(user=self.user1, quiz=self.quiz)
        attempt2 = QuizAttempt.objects.create(user=self.user2, quiz=self.quiz)
        
        # User1 should only see their attempt
        self.authenticate(self.user1)
        url = reverse('quiz:attempt-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], attempt1.id)
        
        # User2 should only see their attempt
        self.authenticate(self.user2)
        response = self.client.get(url)

        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], attempt2.id)


    def test_access_other_user_attempt(self):
        attempt = QuizAttempt.objects.create(user=self.user1, quiz=self.quiz)
        
        self.authenticate(self.user2)
        url = reverse('quiz:attempt-detail', args=[attempt.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

# Integration test for complete workflow
class QuizWorkflowIntegrationTest(QuizAPITestCase):

    def test_complete_workflow(self):
        
        # 1. User1 creates a quiz
        self.authenticate(self.user1)
        create_url = reverse('quiz:quiz-list-create')
        
        quiz_data = {
            'title': 'Integration Test Quiz',
            'description': 'Testing the complete workflow',
            'time_limit': 10,
            'max_attempts': 1,
            'questions': [
                {
                    'text': 'What is the capital of France?',
                    'question_type': 'single_choice',
                    'points': 20,
                    'order': 1,
                    'answers': [
                        {'text': 'London', 'is_correct': False},
                        {'text': 'Paris', 'is_correct': True, 'explanation': 'Paris is the capital of France'},
                        {'text': 'Berlin', 'is_correct': False},
                        {'text': 'Madrid', 'is_correct': False}
                    ]
                },
                {
                    'text': 'Which are prime numbers?',
                    'question_type': 'multiple_choice',
                    'points': 30,
                    'order': 2,
                    'answers': [
                        {'text': '2', 'is_correct': True},
                        {'text': '3', 'is_correct': True},
                        {'text': '4', 'is_correct': False},
                        {'text': '5', 'is_correct': True}
                    ]
                }
            ]
        }
        
        response = self.client.post(create_url, quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_quiz_id = response.data['id']

        # 2. User2 discovers and takes the quiz
        self.authenticate(self.user2)
        
        # List quizzes
        list_url = reverse('quiz:quiz-list-create')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Original + new
        
        # Get quiz for taking
        take_url = reverse('quiz:quiz-take', args=[new_quiz_id])
        response = self.client.get(take_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Start attempt
        attempt_url = reverse('quiz:attempt-list-create')
        response = self.client.post(
            attempt_url, 
            {'quiz_id': new_quiz_id}, 
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        attempt_id = response.data['id']
        
        # Submit answers (get some right, some wrong)
        quiz = Quiz.objects.get(id=new_quiz_id)
        question1 = quiz.questions.get(order=1)
        question2 = quiz.questions.get(order=2)
        
        correct_answer1 = question1.answers.get(text='Paris')
        wrong_answer2 = question2.answers.get(text='4')  # Wrong answer
        
        submit_url = reverse('quiz:quiz-submit', args=[attempt_id])
        submission_data = {
            'answers': [
                {
                    'question': question1.id,
                    'selected_answer': correct_answer1.id
                },
                {
                    'question': question2.id,
                    'selected_answer': wrong_answer2.id
                }
            ]
        }

        response = self.client.post(submit_url, submission_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['correct_answers'], 1)
        self.assertEqual(response.data['total_questions'], 2)
        
        # Check calculated score (20 out of 50 points = 40%)
        expected_score = (20 / 50) * 100
        self.assertEqual(response.data['score'], expected_score)
        
        # 3. Get detailed results
        results_url = reverse('quiz:quiz-results', args=[attempt_id])
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify result details
        user_answers = response.data['user_answers']
        self.assertEqual(len(user_answers), 2)
        self.assertTrue(user_answers[0]['is_correct'])  # First answer correct
        self.assertFalse(user_answers[1]['is_correct'])  # Second answer wrong

        # 4. Check dashboard
        dashboard_url = reverse('quiz:user-dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stats']['completed_quizzes'], 1)
        self.assertEqual(response.data['stats']['average_score'], expected_score)
        
        # 5. User1 checks quiz stats
        self.authenticate(self.user1)
        stats_url = reverse('quiz:quiz-stats', args=[new_quiz_id])
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_attempts'], 1)
        self.assertEqual(response.data['average_score'], expected_score)

# Performance and edge case tests
class QuizPerformanceTests(QuizAPITestCase):
    
    def test_large_quiz_performance(self):
        self.authenticate(self.user1)
        
        # Create quiz with 50 questions
        large_quiz = Quiz.objects.create(title='Large Quiz',created_by=self.user1)

        questions = []
        for i in range(50):
            question = Question.objects.create(quiz=large_quiz,text=f'Question {i+1}?',question_type='single_choice',points=2,order=i+1)
            questions.append(question)


            # Add answers
            for j, (text, is_correct) in enumerate([
                ('Option A', j == 0), ('Option B', j == 1), 
                ('Option C', j == 2), ('Option D', j == 3)
            ]):
                Answer.objects.create(question=question,text=text,is_correct=is_correct)

                 # Test retrieval performance
        url = reverse('quiz:quiz-detail', args=[large_quiz.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['questions']), 50)
        
        # Test taking the quiz
        self.authenticate(self.user2)
        take_url = reverse('quiz:quiz-take', args=[large_quiz.id])
        response = self.client.get(take_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should not show correct answers
        for question in response.data['questions']:
            for answer in question['answers']:
                self.assertNotIn('is_correct', answer)

    
if __name__ == '__main__':
    # Run specific test
    # python manage.py test quiz.tests.QuizWorkflowIntegrationTest.test_complete_workflow
    pass


        
        

        



    







