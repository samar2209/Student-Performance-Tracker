import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from models import db, Student, Grade, StudentTracker

def create_app():
    app = Flask(__name__)

    # Secret key for session (used by flash messages)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'devkey')

    # Database configuration: use Render's DATABASE_URL or fallback to local sqlite
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///students.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Create database tables if not exist
    with app.app_context():
        db.create_all()

    tracker = StudentTracker()

    # -------------------- ROUTES --------------------

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/students')
    def list_students():
        students = Student.query.all()
        return render_template('list_students.html', students=students)

    @app.route('/add_student', methods=['GET', 'POST'])
    def add_student():
        if request.method == 'POST':
            name = request.form['name']
            roll_number = request.form['roll_number']
            if not name or not roll_number:
                flash("Name and Roll Number are required.", "error")
                return redirect(url_for('add_student'))

            try:
                tracker.add_student(name, roll_number)
                flash("Student added successfully!", "success")
                return redirect(url_for('list_students'))
            except Exception as e:
                flash(f"Error: {e}", "error")
                return redirect(url_for('add_student'))

        return render_template('add_student.html')

    @app.route('/add_grade', methods=['GET', 'POST'])
    def add_grade():
        if request.method == 'POST':
            roll_number = request.form['roll_number']
            subject = request.form['subject']
            grade = request.form['grade']

            if not roll_number or not subject or not grade:
                flash("All fields are required.", "error")
                return redirect(url_for('add_grade'))

            try:
                grade = float(grade)
                if grade < 0 or grade > 100:
                    flash("Grade must be between 0 and 100.", "error")
                    return redirect(url_for('add_grade'))

                tracker.add_grades(roll_number, subject, grade)
                flash("Grade added successfully!", "success")
                return redirect(url_for('student_details', roll_number=roll_number))
            except Exception as e:
                flash(f"Error: {e}", "error")
                return redirect(url_for('add_grade'))

        return render_template('add_grade.html')

    @app.route('/student/<roll_number>')
    def student_details(roll_number):
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student:
            flash("Student not found.", "error")
            return redirect(url_for('list_students'))
        return render_template('view_student.html', student=student, grades=student.grades)

    @app.route('/average/<roll_number>')
    def average(roll_number):
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student:
            flash("Student not found.", "error")
            return redirect(url_for('list_students'))
        average = student.calculate_average()
        return render_template('average.html', student=student, average=average)

    return app

# Run locally
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
