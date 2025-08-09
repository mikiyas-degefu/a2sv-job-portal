# API Documentation

## Base URL

All endpoints are prefixed with `/api/`

---

## Jobs

### Create a Job  
**POST** `/api/jobs/`  
_Create a new job posting (company users only)._

---

### Browse Jobs  
**GET** `/api/jobs/browse/`  
_List all open jobs with optional filters._  

**Query parameters:**  
- `title` (string, optional) — Case-insensitive substring search on job title  
- `location` (string, optional) — Case-insensitive substring search on location  
- `company` (string, optional) — Case-insensitive match on company name  
- `page` (int, optional) — Page number, default is 1  
- `page_size` (int, optional) — Number of items per page, default is 10  

---

### Job Details  
**GET** `/api/jobs/<int:job_id>/`  
_Get detailed information for a specific job posting._  

---

### Apply to a Job  
**POST** `/api/jobs/apply/`  
_Apply for a job (applicant role only)._

**Request Body:**  
- `job` (int, required) — ID of the job to apply to  
- `resume_link` (string, required) — URL to the applicant's resume (PDF or DOCX)  
- `cover_letter` (string, optional) — Cover letter text, max 200 characters  

---

### View My Posted Jobs  
**GET** `/api/jobs/my/`  
_Company users can view all jobs they have posted._  

**Query parameters:**  
- `status` (string, optional) — Filter by job status (`open`, `closed`)  
- `page` (int, optional) — Page number, default 1  
- `page_size` (int, optional) — Number of items per page, default 10  

---

### View Job Applications (Company Only)  
**GET** `/api/jobs/<int:job_id>/applications/`  
_View applications submitted for a specific job._  

**Query parameters:**  
- `status` (string, optional) — Filter applications by their status  
- `page` (int, optional), `page_size` (int, optional) — Pagination options  

---

## Applications

### Track My Applications (Applicant Only)  
**GET** `/api/applications/my/`  
_List all applications submitted by the logged-in applicant with filters and sorting._  

**Query parameters:**  
- `company` (string, optional) — Filter by company name  
- `job_status` (string, optional) — Filter jobs by status (`open`, `closed`)  
- `application_status` (list of strings, optional) — Filter applications by status (`applied`, `reviewed`, `rejected`, `hired`)  
- `ordering` (string, optional) — Sort results by one of: `appliedAt`, `company`, `status`, `job_title`. Prefix with `-` for descending order  
- `page` (int, optional), `page_size` (int, optional) — Pagination options  

---

### Update Application Status (Company Only)  
**PATCH** `/api/applications/<int:application_id>/status/`  
_Update the status of a job application (company must own the job)._

**Request Body:**  
- `status` (string, required) — One of `applied`, `reviewed`, `interview`, `rejected`, `hired`  

_This endpoint sends an email notification to the applicant if the status is changed to `interview`, `rejected`, or `hired`._

---

## Authentication & Permissions

- All endpoints require authentication.
- Applicants and company users have role-based access to relevant endpoints.
- Only applicants can apply for jobs.
- Only companies can create jobs and manage applications for their jobs.

---

## Pagination Format

List endpoints use pagination with the following response structure:

```json
{
  "count": total_items,
  "next": "next_page_url" | null,
  "previous": "previous_page_url" | null,
  "results": [
    { /* item data */ }
  ]
}
