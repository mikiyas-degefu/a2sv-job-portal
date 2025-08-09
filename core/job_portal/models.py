from django.db import models
from accounts.models import User

class Job(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='draft')
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)   

    def __str__(self):
        return self.title
    

class Application(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('reviewed', 'Reviewed'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    )

    applicant = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='applications')
    job = models.ForeignKey(Job, null=True, on_delete=models.SET_NULL, related_name='applications')
    resume_link = models.URLField()
    cover_letter = models.TextField(null=True, blank=True, max_length=500)
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application of {self.applicant.email} for {self.job.title} - {self.status}"
