from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import initiate_transaction, TransactionHistoryView

app_name = 'api'

urlpatterns=[
    path('initiate/', initiate_transaction),
    path('history/', TransactionHistoryView.as_view()),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]