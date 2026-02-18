"""Views for the affiliates app."""
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AffiliateProfile, Referral, Commission
from .serializers import AffiliateProfileSerializer, ReferralSerializer, CommissionSerializer


class AffiliateProfileView(APIView):
    """Get current user's affiliate profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.affiliate_profile
        except AffiliateProfile.DoesNotExist:
            profile = AffiliateProfile.objects.create(user=request.user)
        return Response(AffiliateProfileSerializer(profile).data)


class ReferralListView(generics.ListAPIView):
    """List users referred by current user."""
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)


class CommissionListView(generics.ListAPIView):
    """List commissions earned by current user."""
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Commission.objects.filter(referral__referrer=self.request.user)
