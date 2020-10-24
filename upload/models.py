from django.contrib.auth.models import User
from django.db import models

DEADLINE_CHOICES = [
    ('passed', 'Passed'),
    ('active', 'Still active'),
]


class Course(models.Model):
    name = models.CharField(max_length=100)
    ID = models.CharField(max_length=30, primary_key=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    ID = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=20)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('student_id', 'course'),)

    def __str__(self):
        return self.student_id + '(' + self.firstName + ' ' + self.lastName + ')'


class CourseAssignments(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    deadline = models.CharField(max_length=20, choices=DEADLINE_CHOICES, default='active')

    def __str__(self):
        return self.name


class Assignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    assignment = models.ForeignKey(CourseAssignments, on_delete=models.CASCADE, default=None)
    file = models.FileField(upload_to='uploaded_files/')
    uploadDate = models.DateTimeField(auto_now_add=True)
    last_upload = models.BooleanField(default=True)
    score = models.FloatField(null=True)

    def __str__(self):
        return self.assignment.__str__() + ' - ' + self.student.__str__()
