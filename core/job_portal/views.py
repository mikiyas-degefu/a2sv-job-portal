from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from django.core.mail import send_mail
from django.db.models import Count
from rest_framework import status as http_status

class JobPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'  
    max_page_size = 100

def base_response(success, message, obj=None, errors=None):
    return {
        "success": success,
        "message": message,
        "object": obj or {},
        "errors": errors or {}
    }

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def job_create_view(request):
    user = request.user
    if user.role != 'company':
        return Response(base_response(False, "Unauthorized access"), status=403)

    serializer = JobCreateSerializer(data=request.data)
    if serializer.is_valid():
        job = serializer.save(created_by=user)
        return Response(base_response(True, "Job created successfully", serializer.data), status=201)
    return Response(base_response(False, "Creation failed", errors=serializer.errors), status=400)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def job_detail_view(request, job_id):
    user = request.user

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response(base_response(False, "Job not found"), status=404)

    if request.method == 'GET':
        serializer = JobSerializer(job)
        return Response(base_response(True, "Job retrieved successfully", serializer.data), status=200)

    # For PATCH and DELETE, check role and ownership
    if user.role != 'company' or job.created_by != user:
        return Response(base_response(False, "Unauthorized access"), status=403)

    if request.method == 'PATCH':
        serializer = JobUpdateSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(base_response(True, "Job updated successfully", serializer.data), status=200)
        return Response(base_response(False, "Update failed", errors=serializer.errors), status=400)

    if request.method == 'DELETE':
        job.delete()
        return Response(base_response(True, "Job deleted successfully"), status=200)
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def browse_jobs_view(request):
    queryset = Job.objects.filter(status='open')

    title = request.query_params.get('title')
    location = request.query_params.get('location')
    company = request.query_params.get('company')

    if title:
        queryset = queryset.filter(title__icontains=title)
    if location:
        queryset = queryset.filter(location__icontains=location)
    if company:
        queryset = queryset.filter(created_by__first_name__icontains=company)

    paginator = JobPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = JobSerializer(page, many=True)

    paginated_response = paginator.get_paginated_response(serializer.data)

    paginated_response.data['results'] = base_response(
        True,
        "Jobs retrieved successfully",
        obj=serializer.data
    )
    return paginated_response



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_job_view(request):
    user = request.user

    if user.role != 'applicant':
        return Response(base_response(False, "Only applicants can apply for jobs."), status=status.HTTP_403_FORBIDDEN)

    serializer = ApplicationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        application = serializer.save()

        company_email = application.job.created_by.email
        job_title = application.job.title
        applicant_email = user.email

        # Optional: you could use try-except around send_mail here
        send_mail(
            subject=f"New Application for {job_title}",
            message=f"You have received a new application from {applicant_email} for your job posting: {job_title}.",
            from_email='mikiyasmebrate@gmail.com',
            recipient_list=[company_email],
            fail_silently=True,
        )

        return Response(base_response(True, "Application submitted successfully.", {
            'application_id': application.id,
            'job': application.job.id,
            'resume_link': application.resume_link,
            'cover_letter': application.cover_letter,
            'status': application.status,
            'applied_at': application.applied_at,
        }), status=status.HTTP_201_CREATED)

    return Response(base_response(False, "Application failed.", errors=serializer.errors), status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def track_my_applications_view(request):
    user = request.user

    if user.role != 'applicant':
        return Response(base_response(False, "Unauthorized access."), status=403)

    queryset = Application.objects.filter(applicant=user)

    # Filters
    company_name = request.query_params.get('company_name')
    job_status = request.query_params.get('job_status')  # expected 'closed' or 'open'
    application_statuses = request.query_params.getlist('application_status')  # list of statuses
    sort_by = request.query_params.get('sort_by', 'applied_at')  # default sort

    if company_name:
        queryset = queryset.filter(job__created_by__first_name__icontains=company_name)

    if job_status:
        queryset = queryset.filter(job__status__iexact=job_status)

    if application_statuses:
        queryset = queryset.filter(status__in=application_statuses)

    allowed_sorts = ['applied_at', '-applied_at', 'company_name', '-company_name', 'status', '-status', 'job_title', '-job_title']
    ordering_map = {
        'company_name': 'job__created_by__first_name',
        '-company_name': '-job__created_by__first_name',
        'job_title': 'job__title',
        '-job_title': '-job__title',
        'status': 'status',
        '-status': '-status',
        'applied_at': 'applied_at',
        '-applied_at': '-applied_at',
    }

    if sort_by not in allowed_sorts:
        sort_by = 'applied_at'

    queryset = queryset.order_by(ordering_map[sort_by])

    # Pagination
    paginator = JobPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = ApplicationListSerializer(page, many=True)

    return paginator.get_paginated_response({
        "success": True,
        "message": "Applications retrieved successfully.",
        "object": serializer.data,
        "errors": {}
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_posted_jobs_view(request):
    user = request.user

    if user.role != 'company':
        return Response(base_response(False, "Unauthorized access."), status=403)

    queryset = Job.objects.filter(created_by=user)

    # Filter by job status if provided
    job_status = request.query_params.get('status')
    if job_status:
        queryset = queryset.filter(status__iexact=job_status)

    # Annotate application count
    queryset = queryset.annotate(application_count=Count('applications'))

    # Pagination
    paginator = JobPagination()
    page = paginator.paginate_queryset(queryset, request)

    serializer = CompanyJobListSerializer(page, many=True)

    return paginator.get_paginated_response({
        "success": True,
        "message": "Jobs retrieved successfully.",
        "object": serializer.data,
        "errors": {}
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_detail_view(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response(
            base_response(False, "Job not found.", None),
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = JobDetailSerializer(job)
    return Response(
        base_response(True, "Job details retrieved successfully.", serializer.data),
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_applications_view(request, job_id):
    user = request.user

    if user.role != 'company':
        return Response(base_response(False, "Unauthorized access", None), status=status.HTTP_403_FORBIDDEN)

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response(base_response(False, "Job not found.", None), status=status.HTTP_404_NOT_FOUND)

    if job.created_by != user:
        return Response(base_response(False, "Unauthorized access", None), status=status.HTTP_403_FORBIDDEN)

    # Filter applications by status if provided
    status_filter = request.query_params.get('status')
    applications_qs = job.applications.all()

    if status_filter:
        applications_qs = applications_qs.filter(status=status_filter)

    paginator = JobPagination()
    page = paginator.paginate_queryset(applications_qs, request)
    serializer = JobApplicationSerializer(page, many=True)

    return paginator.get_paginated_response(base_response(True, "Applications retrieved successfully", serializer.data))




from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

VALID_STATUSES = ['applied', 'reviewed', 'interview', 'rejected', 'hired']

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_application_status_view(request, application_id):
    user = request.user

    new_status = request.data.get('status', '').lower()
    if not new_status:
        return Response(base_response(False, "New status is required"), status=status.HTTP_400_BAD_REQUEST)

    if new_status not in VALID_STATUSES:
        return Response(base_response(False, f"Invalid status '{new_status}'. Must be one of: {', '.join(VALID_STATUSES)}"), status=status.HTTP_400_BAD_REQUEST)

    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        return Response(base_response(False, "Application not found"), status=status.HTTP_404_NOT_FOUND)

    # Check if application has a job
    if application.job is None:
        return Response(base_response(False, "Job for this application does not exist"), status=status.HTTP_400_BAD_REQUEST)

    # Check if the user owns the job
    if application.job.created_by != user:
        return Response(base_response(False, "Unauthorized"), status=status.HTTP_403_FORBIDDEN)

    # Only update if status is different
    if application.status == new_status:
        return Response(base_response(False, "Status is already set to the given value"), status=status.HTTP_400_BAD_REQUEST)

    # Update status
    application.status = new_status
    application.save()

    # Prepare email notification if status is one of these
    email_messages = {
        'interview': "You’ve been selected for an interview!",
        'rejected': "We regret to inform you that your application was not successful.",
        'hired': "Congratulations! You’ve been hired.",
    }

    if new_status in email_messages:
        subject = f"Update on your application for {application.job.title}"
        message = (
            f"Dear {application.applicant.first_name},\n\n"
            f"{email_messages[new_status]}\n"
            f"Job Title: {application.job.title}\n"
            f"New Status: {new_status.capitalize()}\n\n"
            "Best regards,\n"
            f"{user.get_full_name()}"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email='mikiyasmebrate@gmail.com',
            recipient_list=[application.applicant.email],
            fail_silently=True,
        )

    data = {
        'application_id': application.id,
        'job': application.job.id,
        'status': application.status,
        'applicant': application.applicant.id,
        'resume_link': application.resume_link,
        'cover_letter': application.cover_letter,
        'applied_at': application.applied_at,
    }

    return Response(base_response(True, "Application status updated successfully.", data), status=status.HTTP_200_OK)
