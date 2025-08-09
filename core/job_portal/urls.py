from django.urls import path
from .views import *

urlpatterns = [
    path('jobs/', job_create_view, name='job-create'),           
    path('jobs/<int:job_id>/', job_detail_view, name='job-detail'), 
    path('jobs/browse/', browse_jobs_view, name='browse-jobs'), 
    path('jobs/apply/', apply_job_view, name='apply-job'),   
    path('applications/my/', track_my_applications_view, name='track-my-applications'),
    path('jobs/my/', my_posted_jobs_view, name='my-posted-jobs'),
    path('jobs/<int:job_id>/', job_detail_view, name='job-detail'),
    path('jobs/<int:job_id>/applications/', job_applications_view, name='job-applications'),
    path('applications/<int:application_id>/status/', update_application_status_view, name='update-application-status'),
]
