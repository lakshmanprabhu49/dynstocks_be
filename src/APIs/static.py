import os
from flask_restful import abort

def checkXRequestIdHeader(request):
    if('x-request-id' not in request.headers):
        abort(403, message = 'You are unauthorized to make the request')
    XRequestId = request.headers.get("x-request-id")
    if (XRequestId != os.environ.get('DYNSTOCKS_X_REQUEST_ID')):
        abort(403, message = 'You are unauthorized to make the request')