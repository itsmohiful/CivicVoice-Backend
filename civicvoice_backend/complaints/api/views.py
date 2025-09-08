"""
API Root view and documentation.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    API Root - Lists all available endpoints
    """
    return Response({
        'message': 'Welcome to CivicVoice REST API',
        'version': '1.0.0',
        'endpoints': {
            'Authentication': {
                'token_obtain': reverse('token_obtain_pair', request=request, format=format),
                'token_refresh': reverse('token_refresh', request=request, format=format),
                'token_verify': reverse('token_verify', request=request, format=format),
                'register': reverse('user-register', request=request, format=format),
                'me': reverse('user-me', request=request, format=format),
                'users': reverse('user-list', request=request, format=format),
            },
            'Complaints': {
                'categories': reverse('complaintcategory-list', request=request, format=format),
                'subcategories': reverse('complaintsubcategory-list', request=request, format=format),
                'tags': reverse('complainttag-list', request=request, format=format),
                'locations': reverse('location-list', request=request, format=format),
                'complaints': reverse('complaint-list', request=request, format=format),
                'comments': reverse('complaintcomment-list', request=request, format=format),
                'reactions': reverse('complaintreaction-list', request=request, format=format),
                'attachments': reverse('complaintattachment-list', request=request, format=format),
                'shares': reverse('complaintshare-list', request=request, format=format),
                'followers': reverse('complaintfollower-list', request=request, format=format),
                'reports': reverse('complaintreport-list', request=request, format=format),
                'status_history': reverse('complaintstatushistory-list', request=request, format=format),
            }
        },
        'documentation': {
            'graphql': '/graphql/',
            'admin': '/admin/',
        },
        'authentication': {
            'description': 'Use JWT tokens for authentication',
            'header_format': 'Authorization: Bearer <token>',
            'example': {
                'obtain_token': 'POST /api/token/ with username/password',
                'use_token': 'Include "Authorization: Bearer <access_token>" in headers'
            }
        }
    })
