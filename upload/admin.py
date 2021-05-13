from django.contrib import admin
from .models import Student, Assignment, Course, CourseAssignments, StudentsGroup, Poll, PollOption


class DatedAssignment(admin.ModelAdmin):
    readonly_fields = ('uploadDate',)


admin.site.register(Student)
admin.site.register(Assignment, DatedAssignment)
admin.site.register(Course)
admin.site.register(CourseAssignments)
admin.site.register(StudentsGroup)
admin.site.register(Poll)
admin.site.register(PollOption)

