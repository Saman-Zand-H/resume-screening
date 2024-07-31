from account.models import User
from common.utils import fields_join

from django.contrib import admin

from .models import Course, CourseResult


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        Course.name.field.name,
        Course.type.field.name,
        Course.external_id.field.name,
    ]
    search_fields = [Course.name.field.name, Course.external_id.field.name]
    list_filter = [Course.type.field.name, Course.industries.field.name]


@admin.register(CourseResult)
class CourseResultAdmin(admin.ModelAdmin):
    list_display = [
        CourseResult.course.field.name,
        CourseResult.user.field.name,
        CourseResult.status.field.name,
        CourseResult.created_at.field.name,
        CourseResult.updated_at.field.name,
    ]
    search_fields = [
        fields_join(CourseResult.course.field.name, Course.name.field.name),
        fields_join(CourseResult.user.field.name, User.email.field.name),
    ]
    list_filter = [CourseResult.status.field.name]
