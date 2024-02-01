from . import views
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('populate_db', csrf_exempt(views.populate_db), name="populate_db"),
    path('register', csrf_exempt(views.register), name="register"),
    path('view-loan/<int:loan_id>/', csrf_exempt(views.get_loan_info), name="get_loan_info"),
    path('view-loans/<int:customer_id>/', csrf_exempt(views.get_customer_loans_info), name="get_customer_loans_info"),
    path('check-eligibility', csrf_exempt(views.check_eligibility), name="check_eligibility"),
    path('create-loan', csrf_exempt(views.sanction_loan), name="sanction_loan"),
    # path('testing/<int:tid>/', csrf_exempt(views.testing1), name="testing1"),
    # path('testing/4', csrf_exempt(views.testing2), name="testing2"),
    # path('show_current_debt', csrf_exempt(views.show_current_debt), name = "show_current_debt"),
]
