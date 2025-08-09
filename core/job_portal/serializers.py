from rest_framework import serializers
from django.core.exceptions import ValidationError
import re
from .models import *

class JobCreateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(min_length=1, max_length=100)
    description = serializers.CharField(min_length=20, max_length=2000)
    location = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=['draft', 'open'], default='draft')

    class Meta:
        model = Job
        fields = ['title', 'description', 'location', 'status']

    def validate_status(self, value):
        if value not in ['draft', 'open']:
            raise serializers.ValidationError("Status must be 'draft' or 'open' when creating a job.")
        return value
    

class JobUpdateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(min_length=1, max_length=100, required=False)
    description = serializers.CharField(min_length=20, max_length=2000, required=False)
    location = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=['draft', 'open', 'closed'], required=False)

    class Meta:
        model = Job
        fields = ['title', 'description', 'location', 'status']

    def validate_status(self, value):
        job = self.instance
        status_order = ['draft', 'open', 'closed']

        current_index = status_order.index(job.status)
        new_index = status_order.index(value)

        if new_index < current_index:
            raise serializers.ValidationError(
                f"Status transition not allowed. Current status is '{job.status}'. "
                "You cannot revert to a previous status."
            )
        return value


class JobSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField() 

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'location', 'status', 'created_by', 'created_at', 'updated_at']



class ApplicationSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        required=True,
        error_messages={'required': 'Job ID is required.'}
    )
    resume_link = serializers.URLField(required=True)
    cover_letter = serializers.CharField(max_length=500, required=False, allow_blank=True)

    class Meta:
        model = Application
        fields = ['job', 'resume_link', 'cover_letter']

    def validate(self, attrs):
        user = self.context['request'].user
        job = attrs.get('job')

        if Application.objects.filter(applicant=user, job=job).exists():
            raise serializers.ValidationError("You have already applied to this job.")
        return attrs
    

class ApplicationListSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.created_by.first_name', read_only=True)
    job_status = serializers.CharField(source='job.status', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job_title', 'company_name', 'job_status', 'status', 'applied_at']



class CompanyJobListSerializer(serializers.ModelSerializer):
    application_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'location', 'status', 'created_at', 'application_count']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        desc = data.get('description', '')
        data['description'] = desc if len(desc) <= 200 else desc[:197] + '...'
        return data


class JobDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'location', 'status', 'created_at', 'updated_at', 'created_by']

    def get_created_by(self, obj):
        user = obj.created_by
        if user:
            return f"{user.first_name} {user.last_name}".strip()
        return None
    

class JobApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    
    class Meta:
        model = Application
        fields = ['applicant_name', 'resume_link', 'cover_letter', 'status', 'applied_at']


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[choice[0] for choice in Application.STATUS_CHOICES])

    def validate_status(self, value):
        return value.lower()  