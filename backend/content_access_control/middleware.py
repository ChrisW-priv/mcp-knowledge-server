from content_access_control.models import PolicySubject

class PolicySubjectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        subject_name = request.headers.get('X-Policy-Subject-Act-As', 'default')

        # Check if user is authenticated
        if request.user.is_authenticated:
            try:
                policy_subject = PolicySubject.objects.get(user=request.user, name=subject_name)
            except PolicySubject.DoesNotExist:
                policy_subject = None
        else:
            policy_subject = None

        request.policy_subject = policy_subject
        return self.get_response(request)
