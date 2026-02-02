from rest_framework.permissions import BasePermission

class IsSellerOrAdmin(BasePermission):
    def has_permission(self, request, view): #type: ignore
        return (
            request.session.get("seller_id") is not None
        )
    
