from rest_framework import permissions

class IsCreatorOrReadOnly(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the creator
        return obj.creator == request.user

class CanTakeQuiz(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        # Check if user has exceeded max attempts
        user_attempts = obj.attempts.filter( user=request.user, completed_at__isnull=False).count()
        return user_attempts < obj.max_attempts