from account.models import User
from common.utils import fj

from django.contrib import admin

from .models import Course, CourseResult


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        Course.name.field.name,
        Course.external_id.field.name,
        Course.is_required.field.name,
        Course.is_active.field.name,
    ]
    search_fields = [Course.name.field.name, Course.external_id.field.name]
    list_filter = [
        Course.industries.field.name,
        Course.is_required.field.name,
        Course.is_active.field.name,
    ]


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
        fj(CourseResult.course, Course.name),
        fj(CourseResult.user, User.email),
    ]
    list_filter = [CourseResult.status.field.name]
