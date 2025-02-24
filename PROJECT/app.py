from flask import Flask, render_template, redirect, url_for, jsonify, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql.expression import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learnwise.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'student_login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_instructor = db.Column(db.Boolean, default=False)
    expertise = db.Column(db.String(100))  # For instructors
    experience = db.Column(db.Integer)      # For instructors
    courses_created = db.relationship('Course', backref='instructor', lazy=True)
    progress = db.relationship('UserProgress', backref='user', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lessons = db.relationship('Lesson', backref='course', lazy=True)
    image_url = db.Column(db.String(500))

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    order = db.Column(db.Integer)
    quiz = db.relationship('Quiz', backref='lesson', lazy=True, uselist=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    questions = db.relationship('Question', backref='quiz', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(500), nullable=False)
    options = db.Column(db.JSON)  # Store answer options as JSON

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    completed = db.Column(db.Boolean, default=False)
    quiz_score = db.Column(db.Float)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
@app.route('/')
def home():
    # Query for featured courses to display in the carousel
    featured_courses = Course.query.limit(8).all()
    return render_template('base.html', featured_courses=featured_courses)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        fullname = request.form.get('fullname')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('student_signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('student_signup'))
        
        user = User(
            fullname=fullname,
            email=email,
            password=generate_password_hash(password),
            is_instructor=False
        )
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('student_login'))
    return render_template('student_signup.html')


@app.route('/instructor/signup', methods=['GET', 'POST'])
def instructor_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        fullname = request.form.get('fullname')
        expertise = request.form.get('expertise')
        experience = request.form.get('experience')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('instructor_signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('instructor_signup'))
        
        user = User(
            fullname=fullname,
            email=email,
            password=generate_password_hash(password),
            is_instructor=True,
            expertise=expertise,
            experience=experience
        )
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('instructor_login'))
    return render_template('instructor_signup.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, is_instructor=False).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')  # This is already correct
            return redirect(url_for('home'))
        flash('Invalid email or password', 'danger')
        
    return render_template('student_login.html')

@app.route('/instructor/login', methods=['GET', 'POST'])
def instructor_login():
    print("Method:", request.method)  # Debug print
    
    if current_user.is_authenticated:
        print("User already authenticated")  # Debug print
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        print("Form data:", request.form)  # Debug print
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Login attempt - Email: {email}")  # Debug print
        
        user = User.query.filter_by(email=email, is_instructor=True).first()
        if user:
            print("User found in database")  # Debug print
            if check_password_hash(user.password, password):
                print("Password matches")  # Debug print
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                print("Password doesn't match")  # Debug print
        else:
            print("User not found")  # Debug print
            
        flash('Invalid email or password', 'danger')
    return render_template('instructor_login.html')

@app.route('/debug/check-user/<email>')
def check_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({
            'exists': True,
            'is_instructor': user.is_instructor,
            'email': user.email
        })
    return jsonify({'exists': False})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Course Management Routes
@app.route('/instructor/create-course', methods=['GET', 'POST'])
@login_required
def create_course():
    if not current_user.is_instructor:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        course = Course(
            title=request.form.get('title'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            instructor_id=current_user.id,
            price=float(request.form.get('price'))
        )
        db.session.add(course)
        db.session.commit()
        return redirect(url_for('add_lesson', course_id=course.id))
    return render_template('create_course.html')

@app.route('/instructor/course/<int:course_id>/add-lesson', methods=['GET', 'POST'])
@login_required
def add_lesson(course_id):
    if not current_user.is_instructor:
        return redirect(url_for('home'))
        
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        lesson = Lesson(
            title=request.form.get('title'),
            content=request.form.get('content'),
            course_id=course_id,
            order=len(course.lessons) + 1
        )
        db.session.add(lesson)
        db.session.commit()
        
        if request.form.get('has_quiz') == 'yes':
            return redirect(url_for('add_quiz', lesson_id=lesson.id))
        return redirect(url_for('instructor_dashboard'))
    return render_template('add_lesson.html', course=course)

@app.route('/instructor/lesson/<int:lesson_id>/add-quiz', methods=['GET', 'POST'])
@login_required
def add_quiz(lesson_id):
    if not current_user.is_instructor:
        return redirect(url_for('home'))
        
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.course.instructor_id != current_user.id:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        # Create a new quiz
        quiz = Quiz(lesson_id=lesson_id)
        db.session.add(quiz)
        db.session.commit()
        
        # Get all form data
        form_data = request.form.to_dict()
        
        # Find and process all questions by their index pattern
        question_indices = set()
        for key in form_data:
            if key.startswith('question-'):
                index = key.split('-')[1]
                question_indices.add(index)
        
        # Process each question
        for idx in question_indices:
            question_text = form_data.get(f'question-{idx}')
            correct_answer = form_data.get(f'correct_answer-{idx}')
            
            # Collect all options for this question
            options = []
            option_index = 1
            while f'option-{idx}-{option_index}' in form_data:
                option_value = form_data.get(f'option-{idx}-{option_index}')
                if option_value:
                    options.append(option_value)
                option_index += 1
            
            # Create the question
            if question_text and correct_answer and options:
                question = Question(
                    quiz_id=quiz.id,
                    question_text=question_text,
                    correct_answer=correct_answer,
                    options=options
                )
                db.session.add(question)
        
        db.session.commit()
        flash('Quiz added successfully!', 'success')
        return redirect(url_for('instructor_dashboard'))
        
    return render_template('add_quiz.html', lesson=lesson)

@app.route('/lesson/<int:lesson_id>/submit-quiz', methods=['POST'])
@login_required
def submit_quiz(lesson_id):
    if current_user.is_instructor:
        return redirect(url_for('home'))
    
    lesson = Lesson.query.get_or_404(lesson_id)
    quiz = Quiz.query.filter_by(lesson_id=lesson_id).first()
    
    if not quiz:
        flash('No quiz found for this lesson', 'error')
        return redirect(url_for('view_lesson', course_id=lesson.course_id, lesson_id=lesson_id))
    
    # Calculate score
    total_questions = len(quiz.questions)
    correct_answers = 0
    
    for question in quiz.questions:
        submitted_answer = request.form.get(f'question_{question.id}')
        if submitted_answer == question.correct_answer:
            correct_answers += 1
    
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Update user progress
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        course_id=lesson.course_id,
        lesson_id=lesson_id
    ).first()
    
    if progress:
        progress.quiz_score = score
        progress.completed = True
        db.session.commit()
        
        flash(f'Quiz submitted! Your score: {score:.1f}%', 'success')
    else:
        flash('Progress not found', 'error')
    
    return redirect(url_for('view_lesson', course_id=lesson.course_id, lesson_id=lesson_id))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_instructor:
        return redirect(url_for('instructor_dashboard'))
        
    # Get all course progress for the student
    progress_data = []
    enrolled_courses = UserProgress.query.filter_by(user_id=current_user.id).all()
    
    for enrollment in enrolled_courses:
        course = Course.query.get(enrollment.course_id)
        completed_lessons = UserProgress.query.filter_by(
            user_id=current_user.id,
            course_id=course.id,
            completed=True
        ).count()
        
        progress_data.append({
            'course': course,
            'completed_lessons': completed_lessons,
            'current_lesson': enrollment.lesson_id
        })
    
    return render_template('student_dashboard.html', progress=progress_data)

@app.route('/instructor/dashboard')
@login_required
def instructor_dashboard():
    if not current_user.is_instructor:
        return redirect(url_for('student_dashboard'))
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    return render_template('instructor_dashboard.html', courses=courses)

@app.route('/search')
def search_courses():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of courses per page
    
    if query:
        # Split the query into words for more flexible matching
        search_terms = query.lower().split()
        
        # Create conditions for exact category match and partial matches
        conditions = []
        
        # Add exact category match condition first
        exact_category_match = Course.category.ilike(query)
        
        # Then add partial matches for title, description, and category
        for term in search_terms:
            conditions.append(Course.title.ilike(f'%{term}%'))
            conditions.append(Course.description.ilike(f'%{term}%'))
            conditions.append(Course.category.ilike(f'%{term}%'))
        
        # Use the updated case syntax
        ordered_query = Course.query.order_by(
            db.case(
                (exact_category_match, 0),
                else_=1
            )
        ).filter(db.or_(*conditions))
        
        # Paginate the results
        pagination = ordered_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        courses = pagination.items
    else:
        # If no query, return empty pagination object
        pagination = Course.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        courses = []
    
    return render_template('search_results.html', 
                         courses=courses, 
                         query=query,
                         pagination=pagination)
    
@app.route('/browse')
def browse_courses():
    # Get a random selection of courses
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of courses per page
    
    # Get total number of courses
    total_courses = Course.query.count()
    
    # Get random courses with pagination
    courses = Course.query.order_by(func.random()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Pass empty query to indicate this is browse mode
    return render_template('search_results.html', 
                         courses=courses.items,
                         pagination=courses,
                         query="")

@app.route('/category/<category>')
def category_courses(category):
    courses = Course.query.filter(Course.category.ilike(f'%{category}%')).all()
    return render_template('search_results.html', courses=courses, query=category)

@app.route('/course/<int:course_id>/enroll')
def enroll_course(course_id):
    if not current_user.is_authenticated:
        flash('Please sign up or log in to enroll in courses', 'info')
        return redirect(url_for('student_signup'))
        
    if current_user.is_instructor:
        flash('Instructors cannot enroll in courses', 'error')
        return redirect(url_for('home'))
        
    # Check if already enrolled
    existing_progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_progress:
        flash('You are already enrolled in this course', 'info')
    else:
        # Get the first lesson of the course
        first_lesson = Lesson.query.filter_by(course_id=course_id, order=1).first()
        
        # Create progress entry
        progress = UserProgress(
            user_id=current_user.id,
            course_id=course_id,
            lesson_id=first_lesson.id if first_lesson else None,
            completed=False
        )
        db.session.add(progress)
        db.session.commit()
        flash('Successfully enrolled in the course!', 'success')
    
    return redirect(url_for('student_dashboard'))

# Add this route to your app.py
@app.route('/course/<int:course_id>/lesson/<int:lesson_id>')
@login_required
def view_lesson(course_id, lesson_id):
    if current_user.is_instructor:
        return redirect(url_for('home'))
    
    # Check if user is enrolled in the course
    enrollment = UserProgress.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        flash('Please enroll in the course first', 'error')
        return redirect(url_for('home'))
    
    # Get the current lesson
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.course_id != course_id:
        return redirect(url_for('home'))
    
    # Get all lessons for the course to show progress
    course_lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()
    
    # Update user's current lesson in progress
    enrollment.lesson_id = lesson_id
    enrollment.last_accessed = datetime.utcnow()
    db.session.commit()
    
    # Get quiz if it exists
    quiz = Quiz.query.filter_by(lesson_id=lesson_id).first()
    
    return render_template('view_lesson.html',
                         lesson=lesson,
                         course_lessons=course_lessons,
                         current_lesson_number=lesson.order,
                         total_lessons=len(course_lessons),
                         quiz=quiz)
    
@app.route('/admin/update-categories')
def update_categories():
    # Update "science and technology" courses to proper categories
    science_tech_courses = Course.query.filter(
        Course.category.ilike('%science%and%technology%')
    ).all()
    
    for course in science_tech_courses:
        # You can decide which category fits better
        if 'programming' in course.title.lower() or 'software' in course.title.lower():
            course.category = 'Technology & Programming'
        else:
            course.category = 'Science & Engineering'
    
    db.session.commit()
    return 'Categories updated successfully'

@app.route('/instructor/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    if not current_user.is_instructor:
        flash('Unauthorized access', 'error')
        return redirect(url_for('home'))
    
    course = Course.query.get_or_404(course_id)
    
    # Verify that the current user owns this course
    if course.instructor_id != current_user.id:
        flash('You do not have permission to delete this course', 'error')
        return redirect(url_for('instructor_dashboard'))
    
    try:
        # Delete related quiz questions first
        for lesson in course.lessons:
            if lesson.quiz:
                Question.query.filter_by(quiz_id=lesson.quiz.id).delete()
                Quiz.query.filter_by(lesson_id=lesson.id).delete()
        
        # Delete lessons
        Lesson.query.filter_by(course_id=course_id).delete()
        
        # Delete user progress
        UserProgress.query.filter_by(course_id=course_id).delete()
        
        # Finally delete the course
        db.session.delete(course)
        db.session.commit()
        
        flash('Course has been successfully deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the course', 'error')
    
    return redirect(url_for('instructor_dashboard'))

@app.route('/instructor/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    if not current_user.is_instructor:
        flash('Unauthorized access', 'error')
        return redirect(url_for('home'))
    
    course = Course.query.get_or_404(course_id)
    
    # Verify that the current user owns this course
    if course.instructor_id != current_user.id:
        flash('You do not have permission to edit this course', 'error')
        return redirect(url_for('edit_course', course_id=course_id))
    
    if request.method == 'POST':
        try:
            course.title = request.form.get('title')
            course.description = request.form.get('description')
            course.category = request.form.get('category')
            course.price = float(request.form.get('price'))
            
            db.session.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('instructor_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the course', 'error')
    
    return render_template('edit_course.html', course=course)

if __name__ == '__main__':
    with app.app_context():
         db.create_all()
    app.run(debug=True)