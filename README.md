# QuizRave API

A Django REST Framework-based quiz application that allows users to create, manage, and take quizzes with real-time scoring and progress tracking.

## Features

- **User Authentication**: JWT-based authentication with registration and login
- **Quiz Management**: Create, update, and manage quizzes
- **Question Types**: Support for multiple choice and true/false questions
- **Quiz Taking**: Complete quiz-taking workflow with answer submission
- **Real-time Scoring**: Automatic scoring and results calculation
- **User Progress**: Track quiz attempts and performance history
- **RESTful API**: Clean, RESTful endpoints with proper HTTP status codes

## Tech Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Token-based authentication
- **API Documentation**: DRF Browsable API

## Quick Start

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <https://github.com/Enaibs99/QuizRaveAPI-Alx_Capstone_Project.git>
   cd QuizRaveAPI
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django djangorestframework
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the API**
   - API Base URL: `http://localhost:8000/api/`
   - Admin Panel: `http://localhost:8000/admin/`

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/login/` | User login | No |
| POST | `/api/auth/logout/` | User logout | Yes |

### Quizzes

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/quizzes/` | List all quizzes | Yes |
| POST | `/api/quizzes/` | Create new quiz | Yes |
| GET | `/api/quizzes/{id}/` | Get quiz details | Yes |
| PUT | `/api/quizzes/{id}/` | Update quiz | Yes |
| DELETE | `/api/quizzes/{id}/` | Delete quiz | Yes |
| GET | `/api/quizzes/my-quizzes/` | Get user's quizzes | Yes |

### Questions

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/quizzes/{quiz_id}/questions/` | List quiz questions | Yes |
| POST | `/api/quizzes/{quiz_id}/questions/` | Add question to quiz | Yes |

### Quiz Attempts

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/quizzes/{quiz_id}/start/` | Start quiz attempt | Yes |
| POST | `/api/attempts/{attempt_id}/submit-answer/` | Submit answer | Yes |
| POST | `/api/attempts/{attempt_id}/complete/` | Complete quiz | Yes |
| GET | `/api/attempts/{attempt_id}/` | Get attempt results | Yes |
| GET | `/api/my-attempts/` | Get user's attempts | Yes |

## API Usage Examples

### 1. User Registration
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### 2. User Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepass123"
  }'
```

Response:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

### 3. Create Quiz
```bash
curl -X POST http://localhost:8000/api/quizzes/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Fundamentals",
    "description": "Test your basic Python knowledge",
    "time_limit": 30
  }'
```

### 4. Add Question
```bash
curl -X POST http://localhost:8000/api/quizzes/1/questions/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the output of print(type([]))?",
    "question_type": "multiple_choice",
    "choices": [
      {"text": "<class '\''list'\''>", "is_correct": true},
      {"text": "<class '\''tuple'\''>", "is_correct": false},
      {"text": "<class '\''dict'\''>", "is_correct": false}
    ]
  }'
```

### 5. Take Quiz
```bash
# Start attempt
curl -X POST http://localhost:8000/api/quizzes/1/start/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

# Submit answer
curl -X POST http://localhost:8000/api/attempts/1/submit-answer/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "question": 1,
    "selected_choices": [1]
  }'

# Complete quiz
curl -X POST http://localhost:8000/api/attempts/1/complete/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

## Data Models

### Quiz
- `title`: String - Quiz title
- `description`: Text - Quiz description
- `time_limit`: Integer - Time limit in minutes
- `created_by`: ForeignKey - Quiz creator
- `created_at`: DateTime - Creation timestamp

### Question
- `quiz`: ForeignKey - Associated quiz
- `text`: Text - Question content
- `question_type`: Choice - Type of question (multiple_choice, true_false)
- `order`: Integer - Question order in quiz

### Choice
- `question`: ForeignKey - Associated question
- `text`: String - Choice text
- `is_correct`: Boolean - Whether choice is correct

### QuizAttempt
- `user`: ForeignKey - User taking quiz
- `quiz`: ForeignKey - Quiz being taken
- `started_at`: DateTime - Start time
- `completed_at`: DateTime - Completion time
- `score`: Integer - Final score
- `status`: Choice - Attempt status (in_progress, completed)

## Development

### Project Structure
```
QuizRaveAPI/
├── manage.py
├── QuizRaveAPI/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── quiz_app/
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    └── migrations/
```

### Running Tests
```bash
python manage.py test
```

### Code Style
This project follows PEP 8 guidelines. Run code formatting with:
```bash
black .
flake8 .
```

## Deployment

### Environment Variables
Create a `.env` file for production:
```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=your-database-url
```

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up production database (PostgreSQL)
- [ ] Configure static files serving
- [ ] Set up proper logging
- [ ] Configure CORS if needed for frontend
- [ ] Set up SSL/HTTPS

## API Response Format

### Success Response
```json
{
  "id": 1,
  "title": "Quiz Title",
  "data": "..."
}
```

### Error Response
```json
{
  "error": "Error message",
  "details": {
    "field": ["Specific error for this field"]
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Common Issues & Troubleshooting

### Server Won't Start
- Check if port 8000 is in use: `python manage.py runserver 8001`
- Ensure migrations are run: `python manage.py migrate`
- Check `ALLOWED_HOSTS` setting if `DEBUG=False`

### Authentication Issues
- Ensure token is included in Authorization header: `Authorization: Token <your-token>`
- Check if user is authenticated for protected endpoints

### Database Issues
- Run migrations: `python manage.py makemigrations && python manage.py migrate`
- Reset database: `rm db.sqlite3` then re-run migrations

### API Testing
- Use DRF browsable API: Visit endpoints in browser
- Use Postman or similar tools for API testing
- Check Django admin panel for data verification

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please open an issue in the GitHub repository.