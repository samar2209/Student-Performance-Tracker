from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from typing import Dict, Optional

db = SQLAlchemy()

def init_db(app):
    """Create tables if they do not exist."""
    with app.app_context():
        db.create_all()

class Student(db.Model):
    """
    Student entity (OOP + ORM)
    - Attributes: name, roll_number
    - Relationship: grades (list of Grade)
    - Helper methods: to_dict(), grades_as_dict()
    """
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)

    # Relationship: one-to-many with Grade
    grades = db.relationship("Grade", backref="student", cascade="all, delete-orphan", lazy=True)

    def add_grade(self, subject: str, grade: float):
        """Add or update a grade for the given subject."""
        # Validate subject and grade
        subject = (subject or "").strip()
        if not subject:
            raise ValueError("Subject cannot be empty.")
        if grade < 0 or grade > 100:
            raise ValueError("Grade must be between 0 and 100.")

        # Upsert: if grade for subject exists, update; else insert
        existing = next((g for g in self.grades if g.subject.lower() == subject.lower()), None)
        if existing:
            existing.grade = grade
        else:
            self.grades.append(Grade(subject=subject, grade=grade))

    def calculate_average(self) -> Optional[float]:
        """Calculate average grade across all subjects. Returns None if no grades."""
        if not self.grades:
            return None
        total = sum(g.grade for g in self.grades)
        return round(total / len(self.grades), 2)

    def grades_as_dict(self) -> Dict[str, float]:
        """Return grades as {subject: grade}."""
        return {g.subject: g.grade for g in self.grades}

    def to_dict(self):
        return {
            "roll_number": self.roll_number,
            "name": self.name,
            "grades": self.grades_as_dict(),
            "average": self.calculate_average(),
        }

class Grade(db.Model):
    """
    Grade entity
    - Links to a Student via student_id
    - Subject+Student uniqueness is enforced
    """
    __tablename__ = "grades"
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Float, nullable=False)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "subject", name="uq_student_subject"),
    )

class StudentTracker:
    """
    Service/Manager class to handle collection-level operations.
    This keeps app.py routes clean and encapsulates domain logic.
    """
    def __init__(self, db_session):
        self.db = db_session

    def add_student(self, name: str, roll_number: str):
        roll_number = (roll_number or "").strip()
        name = (name or "").strip()
        if not name or not roll_number:
            raise ValueError("Name and Roll Number are required.")

        # Uniqueness check
        if Student.query.filter_by(roll_number=roll_number).first():
            raise ValueError(f"Roll number '{roll_number}' already exists.")

        student = Student(name=name, roll_number=roll_number)
        self.db.add(student)
        self.db.commit()

    def add_grades(self, roll_number: str, subject: str, grade: float):
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student:
            raise ValueError(f"No student found with roll number {roll_number}.")
        student.add_grade(subject, grade)
        self.db.commit()

    def view_student_details(self, roll_number: str) -> Dict:
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student:
            raise ValueError(f"No student found with roll number {roll_number}.")
        return student.to_dict()

    def calculate_average(self, roll_number: str) -> Optional[float]:
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student:
            raise ValueError(f"No student found with roll number {roll_number}.")
        return student.calculate_average()

    @staticmethod
    def calculate_average_for_student(student: Student) -> Optional[float]:
        return student.calculate_average()
