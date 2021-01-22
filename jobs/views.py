from django.shortcuts import render
from .models import Job, JobTypes, Cities
from django.http import Http404

# Create your views here.

def joblist(request):
    job_list = Job.objects.order_by('job_type')
    for job in job_list:
        job.city_name = Cities[job.job_city][1]
        job.type_name = JobTypes[job.job_type][1]
    return render(request, 'joblist.html', locals())

def detail(request, job_id):
    try:
        job = Job.objects.get(pk=job_id)
        job.city_name = Cities[job.job_city][1]
    except Job.DoesNotExist:
        raise Http404("Job dest not exist")
    return render(request, 'job.html', locals())