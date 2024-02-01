from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date

# Create your models here.
# def validate_customer_id(data):
#     data = str(data)
#     if len(data)!=10:
#         raise ValidationError("customer_id: {} is not of length 10".format(data))
#     if data.isalnum()==False:
#         raise ValidationError("customer_id: {} contains special character(s), only alphanumeric characters are allowed".format(data))

# def validate_loan_id(data):
#     data = str(data)
#     if len(data)!=3:
#         raise ValidationError("loan_id: {} is not of length 3".format(data))
#     if data.isnum()==False:
#         raise ValidationError("loan_id: {} must have only numeric value".format(data))


def validate_phone_number(data):
    data = str(data)
    if data.isnumeric()==False:
        raise ValidationError("Phone number must be numeric.")
    if len(data)<10:
        raise ValidationError("Phone number must be of length 10.")
    
    
def validate_age(data):
    data = int(data)
    if data>150:
        raise ValidationError("Age value {} is too high.".format(data))
    


class customer(models.Model):
    customer_id = models.AutoField(unique = True, primary_key = True)
    first_name = models.CharField(max_length = 20, null = False)
    last_name = models.CharField(max_length = 20, null = True)
    age = models.PositiveSmallIntegerField(validators = [validate_age], null  =True)
    phone_number = models.CharField(unique = True, null = False, validators = [validate_phone_number], max_length = 10)
    monthly_salary = models.PositiveIntegerField(null = True)
    approved_limit = models.PositiveIntegerField(null = True)
    current_debt = models.PositiveIntegerField(null = True, default = 0)

class loan_detail(models.Model):
    customer = models.ForeignKey(customer, on_delete=models.CASCADE)
    loan_id = models.PositiveSmallIntegerField(null = False)
    loan_amount = models.PositiveIntegerField(null = False)
    tenure = models.PositiveSmallIntegerField(null = False)
    interest_rate = models.DecimalField(null = False, max_digits = 5, decimal_places = 2, validators = [MinValueValidator(0), MaxValueValidator(100)])
    emi = models.PositiveIntegerField(verbose_name = "Monthly payment")
    emis_paid_on_time = models.PositiveIntegerField()
    start_date = models.DateField(null = True, verbose_name = "Date of approval", default = date.today())
    end_date = models.DateField(null = True, default = date.today())
    class Meta:
        unique_together = [["customer_id", "loan_id"]]
