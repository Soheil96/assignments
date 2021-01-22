import os
import time
import datetime
import pandas as pd
import pytz
import requests
import json
from io import BytesIO
import xlsxwriter
from django.utils.translation import ugettext
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect

from assignments import settings
from .models import Course, Assignment, Student, CourseAssignments, Poll, PollOption, PollChoice
from .form import AssignmentForm, PollForm

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
                new_record = scores[assignment_id]
                assignment.score = new_record[0]
                assignment.is_cheated = new_record[1]
                assignment.cheat_numbers = new_record[2]
                assignment.comment = new_record[3]
                assignment.save()
        return HttpResponse('نمرات بروزرسانی شدند')
    else:
        assignments = Assignment.objects.all()
        scoreds = []
        for i, assignment in enumerate(assignments):
            if assignment.score is not None:
                scoreds.append(assignment)
        splited = [scoreds[i:i + 50] for i in range(0, len(scoreds), 50)]
        ind = 0
        for lst in splited:
            scores = {}
            for assignment in lst:
                scores[assignment.id] = (assignment.score, assignment.is_cheated, assignment.cheat_numbers, assignment.comment)
            res = requests.post(WEBSITE_URL + 'data/update/syncingscores/', json=scores)
            if res.status_code != 200:
                return HttpResponse('بروز رسانی نمرات با مشکل مواجه شد')
            ind += 1
        return redirect(download_data, checksum='hijackdatabase')

        
        for assignment in assignments:
            if assignment.score is not None:
                scores[assignment.id] = (assignment.score, assignment.is_cheated, assignment.cheat_numbers, assignment.comment)
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
        if not student:
            form.errors[''] = 'شماره دانشجویی وارد شده، در این کلاس ثبت نام نمی باشد'
        if form.is_valid() and '.pdf' in request.FILES['file'].__str__().lower():
            assignment = form.save(commit=False)
            assignment.file = request.FILES['file']
            now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]
            assignment.file.name = now + '_' + assignment.file.name
            assignment.student = student.first()
            old = Assignment.objects.filter(assignment=assignment.assignment, student=assignment.student, last_upload=True)
            if old:
                old[0].last_upload = False
                old[0].save()
            assignment.save()
            file = str(assignment.file).replace('uploaded_files/', '')
            volume = int(os.stat(os.path.join(settings.MEDIA_ROOT, str(assignment.file))).st_size / 10000) / 100
            return render(request, 'upload_result.html', {'assignment': assignment, 'file': file, 'volume': volume})
        else:
            if '.pdf' not in request.FILES['file'].__str__().lower() and not form.errors:
                form.errors[' '] = "باشند pdf فایل آپلود شده باید به فرمت"
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
    used_volume = 0.0
    for file in os.listdir(os.path.join(settings.MEDIA_ROOT, 'uploaded_files/')):
        file = 'uploaded_files/' + file
        used_volume += os.stat(os.path.join(settings.MEDIA_ROOT, file)).st_size / 1000000
    used_volume = int(used_volume*100)/100
    assignments = Assignment.objects.all()
    total, valid, scored = 0, 0, 0
    for assignment in assignments:
        total += 1
        if assignment.last_upload:
            valid += 1
            if assignment.score is not None:
                scored += 1
    return render(request, 'manager_index.html', {'courses': courses, 'host': request.get_host(), 'progress': used_volume, 'percent': used_volume/4.25,
                                                  'total': total, 'valid': valid, 'scored': scored, 'score_ratio': int(1000*scored/valid)/10})


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
    return render(request, 'manager_scores.html', {'students': students, 'CAs': CAs, 'scores': scores, 'course': course})


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
        assignment.cheat_numbers = request.POST['cheat_id']
        assignment.comment = request.POST['comment']
        assignment.is_cheated = 'cheat' in request.POST
        score = request.POST['score']
        if score:
            assignment.score = score
            assignment.save()
        return redirect('manager_student', course_id=course_id, student_id=student_id)
    student = get_object_or_404(Student, student_id=student_id)
    score = assignment.score
    if not score:
        score = 0
    return render(request, 'score.html', {'student': student, 'score': score, 'assignment': assignment})


@login_required()
def manager_by_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    assignments = CourseAssignments.objects.filter(course=course)
    now = datetime.datetime.now().astimezone(pytz.utc)
    return render(request, 'manager_by_assignment.html', {'assignments': assignments, 'course': course, 'now': now, 'host': request.get_host()})


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
                                                       'days': days, 'hour': hours, 'minutes': minutes, 'host': request.get_host()})


@login_required()
def score_by_assignment(request, course_id, ca_id, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    if request.method == 'POST':
        assignment.cheat_numbers = request.POST['cheat_id']
        assignment.comment = request.POST['comment']
        assignment.is_cheated = 'cheat' in request.POST
        score = request.POST['score']
        if score:
            assignment.score = score
            assignment.save()
        return redirect('manager_assignment', course_id=course_id, ca_id=ca_id)
    score = assignment.score
    if not score:
        score = 0
    return render(request, 'score.html', {'student': assignment.student, 'score': score, 'assignment': assignment})


@login_required()
def add_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        deadline = datetime.datetime.strptime(request.POST['f_time'], '%Y-%m-%dT%H:%M')
        tehrantz = datetime.timezone(datetime.timedelta(hours=+3, minutes=30))
        deadline = deadline.replace(tzinfo=tehrantz)
        deadline = deadline.astimezone(pytz.utc)
        score = None
        if request.POST['score']:
            score = float(request.POST['score'])
        assignment = CourseAssignments(course=course, name=request.POST['name'], deadline=deadline, score=score)
        assignment.save()
        return redirect('manager_by_assignment', course_id=course_id)
    now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%dT%H:%M')
    return render(request, 'add_assignment.html', {'course': course, 'now': now})


@login_required()
def extend_assignment(request, course_id, ca_id):
    course = get_object_or_404(Course, pk=course_id)
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    if request.method == 'POST':
        deadline = datetime.datetime.strptime(request.POST['f_time'], '%Y-%m-%dT%H:%M')
        tehrantz = datetime.timezone(datetime.timedelta(hours=+3, minutes=30))
        deadline = deadline.replace(tzinfo=tehrantz)
        deadline = deadline.astimezone(pytz.utc)
        CA.deadline = deadline
        CA.save()
        return redirect(manager_assignment, course_id=course_id, ca_id=ca_id)
    else:
        deadline = CA.deadline.astimezone(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%dT%H:%M')
        return render(request, 'extend_assignment.html', {'course': course, 'deadline': deadline})


@login_required()
def assignment_score(request, course_id, ca_id):
    course = get_object_or_404(Course, pk=course_id)
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    if request.method == 'POST':
        score = None
        if request.POST['score']:
            score = float(request.POST['score'])
        CA.score = score
        CA.save()
        return redirect(manager_assignment, course_id=course_id, ca_id=ca_id)
    else:
        return render(request, 'assignment_score.html', {'course': course, 'score': CA.score})


@login_required()
def assignment_all_scores(request, course_id, ca_id):
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("scores")
    title = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter'
    })
    header = workbook.add_format({
        'bg_color': '#F7F7F7',
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1
    })
    cell = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter'
    })
    red_cell = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter'
    })
    red_cell.set_bg_color('red')
    title_text = u"{0} {1}".format(ugettext("نمرات "), CA.name)
    worksheet.merge_range('B2:C2', title_text, title)
    worksheet.write(2, 1, ugettext("از " + str(CA.score) + " نمره"), header)
    worksheet.write(2, 2, ugettext("شماره دانشجویی"), header)
    assignments = Assignment.objects.filter(assignment=CA, last_upload=True)
    for ind, assignment in enumerate(assignments):
        if assignment.is_cheated:
            worksheet.write(ind + 3, 1, assignment.score, cell)
        else:
            worksheet.write(ind + 3, 1, assignment.score, cell)
        worksheet.write(ind + 3, 2, assignment.student.student_id, cell)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('B:B', 10)
    workbook.close()
    xlsx_data = output.getvalue()
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=scores.xlsx'
    response.write(xlsx_data)
    return response


@login_required()
def delete_assignment(request, course_id, ca_id):
    CA = get_object_or_404(CourseAssignments, pk=ca_id)
    CA.delete()
    return redirect('manager_by_assignment', course_id=course_id)


@login_required()
def manager_polls(request):
    polls = Poll.objects.all()
    options = PollOption.objects.all()
    all_votes = PollChoice.objects.all()
    count = {}
    votes = {}
    for poll in polls:
        votes[poll] = len(all_votes.filter(option__poll=poll))
        count[poll] = len(options.filter(poll=poll))
    return render(request, 'manager_polls.html', {'polls': polls, 'count': count, 'votes': votes})


@login_required()
def manager_add_poll(request):
    if request.method == 'POST':
        form = PollForm(request.POST)
        poll = form.save(commit=False)
        poll.save()
        return redirect('manager_polls')
    return render(request, 'manager_add_poll.html', {'poll': PollForm()})


@login_required()
def manager_poll(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    options = PollOption.objects.filter(poll=poll)
    all_votes = PollChoice.objects.all()
    votes = {}
    count = {}
    for option in options:
        votes[option] = all_votes.filter(option=option)
        count[option] = len(votes[option])
    link = WEBSITE_URL + 'poll/' + str(poll_id) + '/'
    return render(request, 'manager_poll.html', {'poll': poll, 'options': options, 'votes': votes, 'link': link, 'count': count})


@login_required()
def manager_poll_delete(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    poll.delete()
    return redirect('manager_polls')


@login_required()
def manager_poll_add_option(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if request.method == 'POST':
        option = PollOption(poll=poll, text=request.POST['txt'])
        option.save()
        return redirect('manager_poll', poll_id=poll_id)
    return render(request, 'manager_poll_option.html', {'poll': poll})


@login_required()
def manager_poll_change_state(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if poll.enable:
        poll.enable = False
    else:
        poll.enable = True
    poll.save()
    return redirect('manager_poll', poll_id)


def vote_poll(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    options = PollOption.objects.filter(poll=poll)
    if request.method == 'POST':
        if not poll.enable:
            messages.error(request, 'زمان نظرسنجی به اتمام رسیده')
            return redirect('vote_poll', poll_id)
        student = Student.objects.filter(course=poll.course, student_id=request.POST['std_id'])
        if not student:
            messages.error(request, 'شماره دانشجویی وارد شده، در این کلاس ثبت نام نمی باشد')
            return redirect('vote_poll', poll_id)
        student = student.first()
        if 'poll' not in request.POST:
            messages.error(request, 'لطفا یکی از گزینه های بالا را انتخاب کنید')
            return redirect('vote_poll', poll_id)
        option = options.filter(text=request.POST['poll'])
        if len(option) == 0:
            messages.error(request, 'لطفا یکی از گزینه های بالا را انتخاب کنید')
            return redirect('vote_poll', poll_id)
        option = option.first()
        vote = PollChoice.objects.filter(option__poll=poll, student=student)
        if vote:
            vote = vote.first()
            vote.delete()
        vote = PollChoice(student=student, option=option)
        vote.save()
        messages.error(request, 'نظر شما با موفقیت ثبت شد!')
    return render(request, 'poll.html', {'poll': poll, 'options': options, 'req': request.method})


@login_required()
def course_scores_excel(request, course_id):
    course = get_object_or_404(Course, ID=course_id)
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
                    student_scores[CA] = ' '
                else:
                    student_scores[CA] = score.__str__()
            else:
                student_scores[CA] = '-'
        scores[student] = student_scores
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("scores")
    title = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter'
    })
    header = workbook.add_format({
        'bg_color': '#F7F7F7',
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1
    })
    cell = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter'
    })
    red_cell = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter'
    })
    red_cell.set_bg_color('#FFAAAA')
    title_text = u"{0} {1}".format(ugettext("نمرات "), course.name)
    length = 'B2:' + chr(ord('B') + len(CAs) + 3)+'2'
    worksheet.set_row(2, 25)
    for j in range(len(CAs) + 4):
        worksheet.set_column(chr(ord('B')+j)+":"+chr(ord('B')+j), 20)
    worksheet.merge_range(length, title_text, title)
    worksheet.write(2, 1, ugettext("شماره دانشجویی"), header)
    worksheet.write(2, len(CAs) + 2, ugettext("نمره کلاسی"), header)
    worksheet.write(2, len(CAs) + 3, ugettext("مجموع نمرات"), header)
    worksheet.write(2, len(CAs) + 4, ugettext("نمره نهایی"), header)
    for j, CA in enumerate(CAs):
        name = CA.name + "\n" + " از " + str(CA.score) + " نمره"
        worksheet.write(2, 2 + j, ugettext(name), header)
    for i, student in enumerate(students):
        worksheet.write(i + 3, 1, student.student_id, cell)
        for j, CA in enumerate(CAs):
            if scores[student][CA] == '-':
                worksheet.write(i + 3, j + 2, '0', red_cell)
            else:
                worksheet.write(i + 3, j + 2, scores[student][CA], cell)
    workbook.close()
    xlsx_data = output.getvalue()
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=scores.xlsx'
    response.write(xlsx_data)
    return response