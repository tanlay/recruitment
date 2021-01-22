from django.contrib import admin
from . models import Job

# Register your models here.
class JobAdmin(admin.ModelAdmin):
    exclude = ('creator', 'created_time', 'updated_time')
    list_display = ('job_name', 'job_type', 'job_city', 'creator', 'created_time', 'updated_time')
    
    def save_model(self, request, obj, form, change):
        obj.creator = request.user
        super().save_model(request, obj, form, change)



admin.site.register(Job, JobAdmin)