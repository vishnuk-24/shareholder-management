from django.urls import include, path
from .views import ShareListView, PaymentModelViewSet, ShareSummaryAndDetailsView
from .views import ShareholderViewSet, ShareModelViewSet

from rest_framework import routers

router = routers.DefaultRouter()
router.register('shareholders', ShareholderViewSet, basename="shareholders")
router.register('shares-list', ShareListView, basename="shares-list")
router.register('shares', ShareModelViewSet, basename="shares")
router.register('payments', PaymentModelViewSet, basename="payments")


urlpatterns = [
    path('', include(router.urls)),
    path('shares-summary-details/', ShareSummaryAndDetailsView.as_view(), name='share-summary-details'),
]
