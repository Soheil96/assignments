import os
import time
import datetime
import pandas as pd
import pytz
import requests
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect

from assignments import settings
from .models import Course, Assignment, Student, CourseAssignments
from .form import AssignmentForm

WEBSITE_URL = 'http://iaumath.pythonanywhere.com/'


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


@csrf_exempt
def download_data(request, checksum):
    if checksum != 'hijackdatabase':
        raise Http404
    if request.method == 'GET':
        res = requests.post(WEBSITE_URL + 'data/download/hijackdatabase/', data={'passcode': 'riskisonmyown!', 'security': 'verylow'})
        if res.status_code != 200:
            return HttpResponse('آپدیت دیتابیس با مشکل مواجه شد')
        open(os.path.join(settings.BASE_DIR, 'db.sqlite3'), 'wb').write(res.content)
        assignments = Assignment.objects.all()
        for assignment in assignments:
            file_path = os.path.join(settings.MEDIA_ROOT, str(assignment.file))
            if not os.path.exists(file_path):
                res = requests.get(WEBSITE_URL+'manager/'+str(assignment.assignment.course.ID)+'/bystudent/'+
                                   str(assignment.student.student_id)+'/download/'+str(assignment.id)+'/pdf/')
                if res.status_code == 200:
                    open(file_path, 'wb').write(res.content)
    else:
        if request.POST['passcode'] == 'riskisonmyown!' and request.POST['security'] == 'verylow':
            file_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type='application/liquid')
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                    return response
    return redirect(manager_index)


@csrf_exempt
def update(request, checksum):
    if checksum != 'syncingscores':
        raise Http404
    if request.method == 'POST':
        scores = json.load(request)
        for assignment_id in scores.keys():
            if Assignment.objects.filter(id=assignment_id).count() > 0:
                assignment = get_object_or_404(Assignment, id=assignment_id)
                assignment.score = scores[assignment_id]
                assignment.save()
        return HttpResponse('نمرات بروزرسانی شدند')
    else:
        assignments = Assignment.objects.all()
        scores = {}
        for assignment in assignments:
            if assignment.score is not None:
                scores[assignment.id] = assignment.score
        res = requests.post(WEBSITE_URL + 'data/update/syncingscores/', json=scores)
        if res.status_code == 200:
            return redirect(download_data, checksum='hijackdatabase')
        else:
            return HttpResponse('بروز رسانی نمرات با مشکل مواجه شد')


def index(request):
    courses = Course.objects.all()
    return render(request, 'index.html', {'courses': courses})


def course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        std_id = request.POST['std_id']
        form = AssignmentForm(course, request.POST, request.FILES)
        student = Student.objects.filter(course=course, student_id=std_id)
        if '.pdf' not in request.FILES['file'].__str__().lower():
            form.errors[' '] = "باشند pdf فایل آپلود شده باید به فرمت"
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
    return render(request, 'manager_index.html', {'courses': courses, 'host': request.get_host()})


@login_required()
def manager_scores(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    students = Student.objects.filter(course=course)
    CAs = CourseAssignments.objects.filter(course=course)
    scores = {}
    for student in students:
        assignments = Assignment.objects.filter(student=student)
        student_scores = {}
        for CA in CAs:
            assignments_by_CA = assignments.filter(assignment=CA)
            if assignments_by_CA:
                score = -1
                for assignment in assignments_by_CA:
                    if assignment.score is not None:
                        score = max(score, assignment.score)
                if score == -1:
                    student_scores[CA] = '?'
                else:
                    student_scores[CA] = score.__str__()
            else:
                student_scores[CA] = '-'
        scores[student] = student_scores
    return render(request, 'manager_scores.html', {'students': students, 'CAs': CAs, 'scores': scores})


@login_required()
def manager_by_student(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    students = Student.objects.filter(course=course)
    return render(request, 'manager_by_student.html', {'students': students, 'course': course, 'host': request.get_host()})


@login_required()
def add_student(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        old_student = Student.objects.filter(student_id=request.POST['std_id'], course=course)
        if old_student.__len__() > 0:
            messages.error(request, 'این شماره دانشجویی در این کلاس می باشد')
        else:
            student = Student()
            student.course = course
            student.student_id = request.POST['std_id']
            student.firstName = request.POST['f_name']
            student.lastName = request.POST['l_name']
            student.save()
            messages.error(request, 'دانشجو به کلاس اضافه شد')
    return render(request, 'add_student.html', {'course': course})


@login_required()
def manager_student(request, course_id, student_id):
    course = get_object_or_404(Course, pk=course_id)
    student = get_object_or_404(Student, course=course, student_id=student_id)
    assignments = Assignment.objects.filter(student=student, assignment__course=course).reverse()
    return render(request, 'manager_student.html', {'student': student, 'assignments': assignments, 'course': course})


def download(request, course_id, student_id, assignment_id, checksum):
    if checksum != 'pdf':
        raise Http404
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    file_path = os.path.join(settings.MEDIA_ROOT, str(assignment.file))
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


@login_required()
def score_by_student(request, course_id, student_id, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    if request.method == 'POST':
        score = request.POST['score']
        if score:
            assignment.score = score
            assignment.save()
        return redirect('manager_student', course_id=course_id, student_id=student_id)
    student = get_object_or_404(Student, student_id=student_id)
    score = assignment.score
    if not score:
        score = 0
    return render(request, 'score.html', {'student': student, 'score': score})


@login_required()
def manager_by_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    assignments = CourseAssignments.objects.filter(course=course)
    now = datetime.datetime.now().astimezone(pytz.utc)
    return render(request, 'manager_by_assignment.html', {'assignments': assignments, 'course': course, 'now': now})


@login_required()
def manager_assignment(request, course_id, ca_id):
    course = get_object_or_404(Course, pk=course_id)
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    assignments = Assignment.objects.filter(assignment=CA)
    deadline = CA.deadline - datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    if deadline.days < 0:
        deadline = datetime.timedelta(0)
    days, hours, minutes = deadline.days, deadline.seconds//3600, ((deadline.seconds+59)//60) % 60
    return render(request, 'manager_assignment.html', {'assignments': assignments, 'course': course, 'CA': CA,
                                                       'days': days, 'hour': hours, 'minutes': minutes})


@login_required()
def extend_assignment(request, course_id, ca_id):
    course = get_object_or_404(Course, pk=course_id)
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    if request.method == 'POST':
        deadline = datetime.datetime.strptime(request.POST['f_time'], '%Y-%m-%dT%H:%M')
        deadline = deadline.astimezone(pytz.utc)
        CA.deadline = deadline
        CA.save()
        return redirect(manager_assignment, course_id=course_id, ca_id=ca_id)
    else:
        deadline = CA.deadline.astimezone(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%dT%H:%M')
        return render(request, 'extend_assignment.html', {'course': course, 'deadline': deadline})


@login_required()
def score_by_assignment(request, course_id, ca_id, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    if request.method == 'POST':
        score = request.POST['score']
        if score:
            assignment.score = score
            assignment.save()
        return redirect('manager_assignment', course_id=course_id, ca_id=ca_id)
    score = assignment.score
    if not score:
        score = 0
    return render(request, 'score.html', {'student': assignment.student, 'score': score})


@login_required()
def add_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        deadline = datetime.datetime.strptime(request.POST['f_time'], '%Y-%m-%dT%H:%M')
        deadline = deadline.astimezone(pytz.utc)
        assignment = CourseAssignments(course=course, name=request.POST['name'], deadline=deadline)
        assignment.save()
        return redirect('manager_by_assignment', course_id=course_id)
    now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%dT%H:%M')
    return render(request, 'add_assignment.html', {'course': course, 'now': now})


@login_required()
def delete_assignment(request, course_id, ca_id):
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    CA.delete()
    return redirect('manager_by_assignment', course_id=course_id)
