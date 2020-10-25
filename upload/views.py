import os
import time
import datetime
import pandas as pd
import pytz
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect

from assignments import settings
from .models import Course, Assignment, Student, CourseAssignments
from .form import AssignmentForm


@login_required()
def add_students(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    xlsx_file = pd.read_excel(os.path.join(settings.MEDIA_ROOT, 'students.xlsx'), sheet_name=None)['Sheet1']
    for row in xlsx_file.iterrows():
        student = Student(course=course, student_id=row[1][0], firstName=row[1][1], lastName=row[1][2])
        student.save()
    return HttpResponse('دانشجو ها به درس اضافه شدند')


@login_required()
def cleanup(request, checksum):
    if checksum != 'backupisonmycomputer':
        raise Http404
    if request.method == 'POST':
        assignments = Assignment.objects.all()
        to_keep = []
        for assignment in assignments:
            diff = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - assignment.uploadDate
            if diff.total_seconds() < 900:
                to_keep.append(assignment.file)
        for file in os.listdir(os.path.join(settings.MEDIA_ROOT, 'uploaded_files/')):
            file = 'uploaded_files/' + file
            if file not in to_keep and time.time() - os.path.getmtime(os.path.join(settings.MEDIA_ROOT, file)) > 900:
                os.remove(os.path.join(settings.MEDIA_ROOT, file))
        return HttpResponse('فایل ها پاک شدند')
    return render(request, 'delete.html')


def index(request):
    courses = Course.objects.all()
    return render(request, 'index.html', {'courses': courses})


def course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        std_id = request.POST['std_id']
        form = AssignmentForm(course, request.POST, request.FILES)
        student = Student.objects.filter(course=course, student_id=std_id)
        if not student:
            form.errors[''] = 'شماره دانشجویی وارد شده، در این کلاس ثبت نام نمی باشد'
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.file = request.FILES['file']
            assignment.student = student.first()
            old = Assignment.objects.filter(assignment=assignment.assignment, student=assignment.student, last_upload=True)
            if old:
                old[0].last_upload = False
                old[0].save()
            assignment.save()
            return render(request, 'upload_result.html', {'assignment': assignment})
        else:
            return render(request, 'upload_result.html', {'assignment': None, 'error': form.errors})
    form = AssignmentForm(course=course)
    return render(request, 'course.html', {'form': form, 'course': course})


def login_page(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('manager_index')
        else:
            messages.error(request, 'نام کاربری و رمز عبور اشتباه می باشد')
            return redirect('login')
    return render(request, 'login.html')


@login_required()
def manager_index(request):
    courses = Course.objects.all()
    return render(request, 'manager_index.html', {'courses': courses})


@login_required()
def manager_by_student(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    students = Student.objects.filter(course=course)
    return render(request, 'manager_by_student.html', {'students': students, 'course': course})


@login_required()
def manager_student(request, course_id, student_id):
    course = get_object_or_404(Course, pk=course_id)
    student = get_object_or_404(Student, course=course, student_id=student_id)
    assignments = Assignment.objects.filter(student=student, assignment__course=course).reverse()
    return render(request, 'manager_student.html', {'student': student, 'assignments': assignments, 'course': course})


@login_required()
def download(request, course_id, student_id, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    print(assignment.file)
    file_path = os.path.join(settings.MEDIA_ROOT, str(assignment.file))
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


@login_required()
def score_by_student(request, course_id, student_id, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        score = request.POST['score']
        if score:
            assignment.score = score
            assignment.save()
        return redirect('manager_student', course_id=course_id, student_id=student_id)
    student = get_object_or_404(Student, pk=student_id)
    return render(request, 'score.html', {'student': student})


@login_required()
def manager_by_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    assignments = CourseAssignments.objects.filter(course=course)
    return render(request, 'manager_by_assignment.html', {'assignments': assignments, 'course': course})


@login_required()
def manager_assignment(request, course_id, ca_id):
    course = get_object_or_404(Course, pk=course_id)
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    assignments = Assignment.objects.filter(assignment=CA)
    return render(request, 'manager_assignment.html', {'assignments': assignments, 'course': course, 'CA': CA})


@login_required()
def score_by_assignment(request, course_id, ca_id, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        score = request.POST['score']
        if score:
            assignment.score = score
            assignment.save()
        return redirect('manager_assignment', course_id=course_id, ca_id=ca_id)
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    return render(request, 'score.html', {'student': assignment.student})


@login_required()
def add_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        assignment = CourseAssignments(course=course, name=request.POST['name'])
        assignment.save()
        return redirect('manager_by_assignment', course_id=course_id)
    return render(request, 'add_assignment.html', {'course': course})


@login_required()
def change_assignment_status(request, course_id, ca_id):
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    if CA.deadline == 'active':
        CA.deadline = 'passed'
    else:
        CA.deadline = 'active'
    CA.save()
    return redirect('manager_assignment', course_id=course_id, ca_id=ca_id)


@login_required()
def delete_assignment(request, course_id, ca_id):
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    CA.delete()
    return redirect('manager_by_assignment', course_id=course_id)
