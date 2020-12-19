from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


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
        return self.student_id + ' (' + self.firstName + ' ' + self.lastName + ')'


class CourseAssignments(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    deadline = models.DateTimeField(default=timezone.now)
    score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class Assignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    assignment = models.ForeignKey(CourseAssignments, on_delete=models.CASCADE, default=None)
    file = models.FileField(upload_to='uploaded_files/')
    uploadDate = models.DateTimeField(auto_now_add=True)
    last_upload = models.BooleanField(default=True)
    score = models.FloatField(null=True, blank=True)
    is_cheated = models.BooleanField(default=False)
    cheat_numbers = models.CharField(max_length=10, null=True, blank=True)
    comment = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.assignment.__str__() + '_' + self.assignment.course.__str__() + ' - ' + self.student.__str__()


class Poll(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enable = models.BooleanField(default=True)
    text = models.TextField(max_length=250)

    def __str__(self):
        return self.course.__str__() + " - " + str(self.id)


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    text = models.CharField(max_length=150)

    def __str__(self):
        return self.poll.__str__() + " - " + self.text


class PollChoice(models.Model):
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
