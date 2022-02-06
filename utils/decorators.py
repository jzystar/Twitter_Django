from rest_framework.response import Response
from rest_framework import status
from functools import wraps


def required_params(method='GET', params=None):
    if params == None:
        params = []
        
    def decorator(view_func):
        # use wraps to pass parameters from view_func to _wrapped_view
        @wraps(view_func)
        # instance is self in list
        def _wrapped_view(instance, request, *args, **kwargs):
            if method.lower() == 'get':
                data = request.query_params
            else:
                data = request.data

            missing_params = [param for param in params if param not in data]
            if missing_params:
                params_str = ", ".join(missing_params)
                return Response({
                    'success': False,
                    'message': 'missing {} in request'.format(params_str),
                },status=status.HTTP_400_BAD_REQUEST)
            # after all the checks, call view_func
            return view_func(instance, request, *args, **kwargs)
        return _wrapped_view
    return decorator