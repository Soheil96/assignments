import magic
from django import forms
from django.core.exceptions import ValidationError
from django.forms import NumberInput, TextInput

from .models import Assignment, Student, CourseAssignments


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = [
            #'student',
            'assignment',
            'file'
        ]
        labels = {
            #'student': 'شماره دانشجویی',
            'assignment': 'تمرین',
            'file': '(pdf فرمت) فایل'
        }

    def __init__(self, course=None, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        #self.fields['student'].widget = TextInput()
        if course:
            #self.fields['student'].queryset = Student.objects.filter(course=course)
            self.fields['assignment'].queryset = CourseAssignments.objects.filter(course=course, deadline='active')

    def clean(self):
        data = super(AssignmentForm, self).clean()
        file = data.get('file')
        filetype = magic.from_buffer(file.read(), mime=True)
        if "application/pdf" not in filetype:
            raise ValidationError("باشند pdf فایل های آپلود شده باید به فرمت")
        return data
