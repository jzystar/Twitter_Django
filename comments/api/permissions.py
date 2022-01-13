from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    # if error, only shows this message
    message = "You do not have the permission to access this object"
    # detail = False, only check has_permission
    # POST /api/comments/ -> create
    # GET /api/comments/ -> list
    def has_permission(self, request, view):
        return True

    # detail = True, check both of has_permission and has_object_permission
    # GET /api/comments/1/ -> retrieve
    # DELETE /api/comments/1/ ->destroy
    # PATCH /api/comments/1/ -> partial_update
    # PUT /api/comments/1/1 -> update
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user