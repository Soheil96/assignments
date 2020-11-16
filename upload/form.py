import magic
from django import forms
from django.core.exceptions import ValidationError
import datetime
import pytz

from .models import Assignment, Student, CourseAssignments


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = [
            'assignment',
            'file'
        ]
        labels = {
            'assignment': 'تمرین',
            'file': '(pdf فرمت) فایل'
        }

    def __init__(self, course=None, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        if course:
            now = datetime.datetime.now().astimezone(pytz.utc) - datetime.timedelta(0, 120)
            self.fields['assignment'].queryset = CourseAssignments.objects.filter(course=course, deadline__gte=now)

    def clean(self):
        data = super(AssignmentForm, self).clean()
        file = data.get('file')
        filetype = magic.from_buffer(file.read(), mime=True)
        if "application/pdf" not in filetype:
            raise ValidationError("باشند pdf فایل آپلود شده باید به فرمت")
        return data
