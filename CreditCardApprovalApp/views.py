from django.http.response import JsonResponse
from .models import customer, loan_detail
import json
import threading
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from datetime import date
from datetime import datetime
from tqdm import tqdm
     
# Create your views here.


def save_file(request_body, file_name):
    file = ""
    for i in request_body.FILES:
        file = request_body.FILES[i]
        break
    # print(request_body.FILES)
    with open(file_name, "wb+") as data_file:
        for chunk in file.chunks():
            data_file.write(chunk)


def calc_new_end_date(loan_object, end_date_present):
    timestamp_format = "%Y-%m-%d %H:%M:%S"
    month_date = {"01": "31",
                  "02": "28",
                  "03": "31",
                  "04": "30",
                  "05": "31",
                  "06": "30",
                  "07": "31",
                  "08": "31",
                  "09": "30",
                  "10": "31",
                  "11": "30",
                  "12": "31"
                  }
    
    if end_date_present:
        e_year, e_month, e_day = str(loan_object.end_date).split("-")
        s_year, s_month, s_day = str(loan_object.start_date).split("-")
        timestamp_format = "%Y-%m-%d %H:%M:%S"
        if (int(e_year)%4==0 and int(e_year)%100!=0) or int(e_year)%400==0:
            # print(e_year)
            month_date["02"] = "29"
        if int(s_day)>int(month_date[e_month]):
            # print(1, s_day, month_date[e_month], loan_object.end_date, loan_object.start_date, str(loan_object.end_date)[:-2] + month_date[e_month] + " 00:00:00", timestamp_format)
            return(datetime.strptime(str(loan_object.end_date)[:-2] + month_date[e_month] + " 00:00:00", timestamp_format).date())
        else:
            # print(12, s_day, month_date[e_month], loan_object.end_date, loan_object.start_date, str(loan_object.end_date)[:-2] + str(loan_object.start_date)[-2:] + " 00:00:00", timestamp_format)
            return(datetime.strptime(str(loan_object.end_date)[:-2] + str(loan_object.start_date)[-2:] + " 00:00:00", timestamp_format).date())

    else:
        s_year, s_month, s_day = str(loan_object.start_date).split("-")
        e_year = str(int(s_year) + int(loan_object.tenure)//12)
        e_month = str(int(s_month) + int(loan_object.tenure)%12)
        if int(e_month)>12:
            e_month = str(int(e_month) - 12)
            e_year = str(int(e_year) + 1)
        if (int(e_year)%4==0 and int(e_year)%100!=0) or int(e_year)%400==0:
            # print(e_year)
            month_date["02"] = "29"
        if len(e_month)==1:
            e_month="0"+e_month
        e_day = str(min(int(s_day), int(month_date[e_month])))
        if len(e_day)==1:
            e_day="0"+e_day
        
        return(datetime.strptime(e_year+"-"+e_month+"-"+e_day + " 00:00:00", timestamp_format).date())
    

def update_current_debt(customer_object):
    try:
        loan_object = customer_object.loan_detail_set.all()
        current_debt = 0
        for loan in loan_object:
            repayments_left = calc_repayments_left(loan.__dict__)
            current_debt += int(int(loan.loan_amount)*repayments_left/int(loan.tenure))
        customer_object.current_debt = current_debt
        customer_object.save()
        return customer_object.current_debt
    except Exception as e:
        return customer_object.current_debt
    

def calc_repayments_left(loan):
    repayments_left = 0
    years = loan["tenure"]//12
    months = loan["tenure"]%12
    end_date = loan["end_date"]
    start_date = loan["start_date"]
    today_date = date.today()
    if end_date and today_date < end_date:
        years = int(str(end_date)[:4]) - int(str(today_date)[:4])
        months = int(str(end_date)[5:7]) - int(str(today_date)[5:7])
        if int(str(today_date)[7:]) < int(str(end_date)[7:]):
            months += 1
        
        repayments_left = years*12 + months
    elif start_date > today_date:
        years = int(str(end_date)[:4]) - int(str(start_date)[:4])
        months = int(str(end_date)[5:7]) - int(str(start_date)[5:7])
        repayments_left = years*12 + months
    else:
        repayments_left = 0
    return repayments_left


def calc_emi(P, R, N):
    R = R/1200
    emi = P*R*((1+R)**N)/(((1+R)**N)-1)
    return(emi)


def calc_current_emis(customer_object):
    total_emis = 0
    loan_object = customer_object.loan_detail_set.all()
    for loan in loan_object:
        if loan.end_date > date.today():
            total_emis += loan.emi
    return total_emis


def add_customer_data(x):
    try:
        customer_object = customer.objects.create(first_name=x["First Name"],
                                                  phone_number=x["Phone Number"]
                                                  )
        if "Customer ID" in x:
            customer_object.customer_id = x["Customer ID"]
        if "Last Name" in x:
            customer_object.last_name = x["Last Name"]
        if "Age" in x:
            customer_object.age = x["Age"]
        if "Monthly Salary" in x:
            customer_object.monthly_salary =x["Monthly Salary"]
        if "Approved Limit" in x:
            customer_object.approved_limit = x["Approved Limit"]
        if "Current Debt" in x:
            customer_object.current_debt = x["Current Debt"]
        customer_object.save()
    except:
        customer_object = None
    return customer_object


def add_loan_data(x):
    try:
        cid = customer.objects.get(customer_id = x["Customer ID"])
        loan_object = None    
        timestamp_format = "%Y-%m-%d %H:%M:%S"
        if "Loan ID" in x:
            loan_object = loan_detail.objects.create(customer = cid, 
                                        loan_id = x["Loan ID"], 
                                        loan_amount = x["Loan Amount"], 
                                        tenure = x["Tenure"], 
                                        interest_rate = x["Interest Rate"], 
                                        emi = x["Monthly payment"], 
                                        emis_paid_on_time = x["EMIs paid on Time"], 
                                        )
        else:
            loan_ids = [loan.loan_id for loan in cid.loan_detail_set.all()]
            if loan_ids!= []:
                loan_id = max(loan_ids) + 1
            else:
                loan_id = 1
            loan_object = loan_detail.objects.create(customer = cid, 
                                        loan_id = loan_id, 
                                        loan_amount = x["Loan Amount"], 
                                        tenure = x["Tenure"], 
                                        interest_rate = x["Interest Rate"], 
                                        emi = x["Monthly payment"], 
                                        emis_paid_on_time = x["EMIs paid on Time"], 
                                        )
            
        if "Date of Approval" in x and str(x["Date of Approval"]).lower()!="nan":
            # print()
            loan_object.start_date = datetime.strptime(str(x["Date of Approval"]), timestamp_format).date()

        if "End Date" in x and str(x["End Date"]).lower()!="nan":
            loan_object.end_date = datetime.strptime(str(x["End Date"]), timestamp_format).date()
            loan_object.end_date = calc_new_end_date(loan_object, True)
        else:
            loan_object.end_date = calc_new_end_date(loan_object, False)


        loan_object.save()
        loan = loan_object.__dict__
        repayments_left = calc_repayments_left(loan)
        cid.current_debt = cid.current_debt + int(int(loan["loan_amount"])*repayments_left/int(loan["tenure"]))
        cid.save()
    except:
        loan_object = None
    return loan_object


def populate_db(request):
    save_file(request, "data.xlsx")
    df = pd.read_excel("data.xlsx")
    db_name = request.POST.get("db_name")
    t1 = threading.Thread(target = db_populate_helper, args = [df, db_name])
    t1.start()
    return JsonResponse({"message": "DB is being populated."})


def db_populate_helper(df, db_name):
    tqdm.pandas()
    if db_name == "customer_details":
        df.progress_apply(lambda x: add_customer_data(x), axis=1)
    elif db_name == "loan_details":
        df.progress_apply(lambda x: add_loan_data(x), axis=1)


def register(request):
    try:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        age = request.POST.get("age")
        phone_number = request.POST.get("phone_number")
        monthly_salary = request.POST.get("monthly_income")
        current_debt = request.POST.get("current_debt")

        if first_name==None or phone_number==None or monthly_salary == None:
            return JsonResponse({"message": "Mandatory parameters missing"}, status=400)

        
        x = {}
        x["First Name"] = first_name
        x["Phone Number"] = phone_number
        x["Monthly Salary"] = int(monthly_salary)
        x["Approved Limit"] = 100000 * round(36 * int(monthly_salary)/100000)
        if last_name:
            x["Last Name"] = last_name 
        if age:
            x["Age"] = age
        if current_debt:
            x["Current Debt"] = current_debt
        customer_object = add_customer_data(x)
        response = {
            "customer_id": customer_object.customer_id,
            "name": customer_object.first_name + " " + customer_object.last_name,
            "age": customer_object.age,
            "monthly_income": customer_object.monthly_salary,
            "approved_limit": customer_object.approved_limit, 
            "phone_number": customer_object.phone_number
        }
        status = 201
    except Exception as e:
        reposne = {}
        print(e)
        status = 409
    return JsonResponse(response, status=status)


def get_loan_info(request, loan_id):
    response = {}
    try:
        loan_object = loan_detail.objects.filter(loan_id=loan_id).values()
        i = 1
        for loan in loan_object:
            customer_object = customer.objects.get(customer_id=int(loan["customer_id"]))
            customer_details = {
                "id": customer_object.customer_id,
                "first_name": customer_object.first_name,
                "last_name": customer_object.last_name,
                "phone_number": customer_object.phone_number,
                "age": customer_object.age
            }
            temp_response = {
                    "loan_id": loan["loan_id"],
                    "customer": customer_details,
                    "loan_amount": loan["loan_amount"],
                    "interest_rate": loan["interest_rate"],
                    "monthly_installment": loan["emi"],
                    "tenure": loan["tenure"]
            }
            response["loan_"+str(i)] = temp_response
            i += 1
        status = 200

    except ObjectDoesNotExist as e:
        print(e)
        status = 404
    except Exception as e:
        print(e)
        status = 400

    return JsonResponse(response, status=status)


def get_customer_loans_info(request, customer_id):
    response = {}
    try:
        customer_object = customer.objects.get(customer_id=customer_id)
        loan_object = customer_object.loan_detail_set.all().values()
        i = 1
        customer_object.current_debt = 0
        for loan in loan_object:
            repayments_left = calc_repayments_left(loan)
            # print(repayments_left, int(loan["loan_amount"]), int(loan["tenure"]), int(loan["loan_amount"])*repayments_left/int(loan["tenure"]))
            customer_object.current_debt = customer_object.current_debt + int(int(loan["loan_amount"])*repayments_left/int(loan["tenure"]))
            customer_object.save()
            temp_response = {
                    "loan_id": loan["loan_id"],
                    "loan_amount": loan["loan_amount"],
                    "interest_rate": loan["interest_rate"],
                    "monthly_installment": loan["emi"],
                    "repayments_left": repayments_left
            }
            response["loan_"+str(i)] = temp_response
            i+=1
        status = 200

    except ObjectDoesNotExist as e:
        print(e)
        status = 404
    except Exception as e:
        print("Exception:", e)
        status = 500

    return JsonResponse(response, status=status)



def calc_credit_score(customer_object):
    credit_score = 0
    message = "Default message"
    try:
        current_debt = update_current_debt(customer_object)
        if current_debt>customer_object.approved_limit:
            credit_score = 0
            message = "Loan limit reached, current loan amount more than approved limit"
        else:
            total_payments_made = 0
            total_timely_replayments = 0
            total_loans = 0
            new_loans = 0
            loan_history = 0
            earliest_loan = date.today()
            loan_object = customer_object.loan_detail_set.all()
            for loan in loan_object:
                total_loans += 1
                repayments_left = calc_repayments_left(loan.__dict__)
                total_payments_made += loan.tenure - repayments_left
                total_timely_replayments += loan.emis_paid_on_time
                if loan.start_date.year <= date.today().year-5:
                    new_loans += 1
                if loan.start_date < earliest_loan:
                    earliest_loan = loan.start_date
                    if loan.start_date.year<1970:
                        loan_history = date.today().year - 1970
                    else:
                        loan_history = date.today().year - loan.start_date.year
            
            if total_loans==0:
                message = "No history to calculate credit score."
            else:
                if total_payments_made==0:
                    timely_payments_ratio = 0
                else:
                    timely_payments_ratio = total_timely_replayments / total_payments_made
                if timely_payments_ratio>1:
                    timely_payments_ratio = 1

                loan_owe_effect = 0.9 - (customer_object.current_debt / customer_object.approved_limit)
                if loan_owe_effect<0:
                    loan_owe_effect = 0
                elif loan_owe_effect>1:
                    loan_owe_effect = 1

                loan_length_effect = timely_payments_ratio * loan_history / (date.today().year - 1970)

                if new_loans>10:
                    new_loans = 10
                new_loan_effect = 0.9 - (new_loans/10)
                if new_loan_effect<0:
                    new_loan_effect = 0
                elif new_loan_effect>1:
                    new_loan_effect = 1

                credit_score = (timely_payments_ratio * 35) + (loan_owe_effect * 30) + (loan_length_effect * 20) + (new_loan_effect * 15)
                message = "Credit score calculated successfully"

    except Exception as e:
        print(e)
        credit_score = 0
        message = "Some internal error in calculating credit score"
    return credit_score, message


def check_eligibility(request, loan_sanction_check = False):
    try:
        message = ""
        customer_id = request.POST.get("customer_id")
        loan_amount = request.POST.get("loan_amount")
        interest_rate = request.POST.get("interest_rate")
        tenure = request.POST.get("tenure")
        if customer_id!=None and loan_amount!=None and interest_rate!=None and tenure!=None:
            loan_amount = int(loan_amount)
            tenure = int(tenure)
            interest_rate = float(interest_rate)
            customer_object = customer.objects.get(customer_id=customer_id)
            if update_current_debt(customer_object) + loan_amount > customer_object.approved_limit:
                approval=False
                corrected_interest_rate = None
                monthly_installment = None
                status = 200
                message = "Approving this loan will cross your approved limit."
            else:
                credit_score, cs_message = calc_credit_score(customer_object)
                total_emi = calc_current_emis(customer_object)
                if total_emi > .5 * customer_object.monthly_salary and credit_score>=10:
                    approval=False
                    corrected_interest_rate = None
                    monthly_installment = None
                    status = 200
                    message = "Total of current EMIs more than 50% of the monthly salary"
                elif credit_score >= 50:
                    approval = True
                    corrected_interest_rate = interest_rate
                    monthly_installment = calc_emi(loan_amount, corrected_interest_rate, tenure)
                    status = 200
                    message = "Your loan is approved successfully"

                elif credit_score < 50 and credit_score >= 30 and interest_rate >= 12:
                    approval = True
                    corrected_interest_rate = interest_rate
                    monthly_installment = calc_emi(loan_amount, corrected_interest_rate, tenure)
                    status = 200
                    message = "Your loan is approved successfully"

                elif credit_score < 50 and credit_score >= 30 and interest_rate < 12:
                    approval = False
                    corrected_interest_rate = 12.0
                    monthly_installment = calc_emi(loan_amount, corrected_interest_rate, tenure)
                    status = 200
                    message = "Your loan cannot be approved due to low credit score for this loan"

                elif credit_score < 30 and credit_score >= 10 and interest_rate >= 16:
                    approval = True
                    corrected_interest_rate = interest_rate
                    monthly_installment = calc_emi(loan_amount, corrected_interest_rate, tenure)
                    status = 200
                    message = "Your loan is approved successfully"

                elif credit_score < 30 and credit_score >= 10 and interest_rate < 16:
                    approval = False
                    corrected_interest_rate = 16.0
                    monthly_installment = calc_emi(loan_amount, corrected_interest_rate, tenure)
                    status = 200
                    message = "Your loan cannot be approved due to low credit score for this loan"

                else:
                    approval=False
                    corrected_interest_rate = None
                    monthly_installment = None
                    status = 200
                    if cs_message != "Credit score calculated successfully":
                        message = cs_message

        else:
            approval=False
            corrected_interest_rate = None
            monthly_installment = None
            status = 400
            message = "Eligibility cannot be checked due to some missing/inappropriate information"

    
    except ObjectDoesNotExist as e:
        approval=False
        corrected_interest_rate = None
        monthly_installment = None
        status = 404
        print(e)
        message = "Customer does not exist"

    except Exception as e:
        approval=False
        corrected_interest_rate = None
        monthly_installment = None
        status = 500
        message = "Some internal error in checking eligibility"
            
    response = {
            "customer_id": customer_id,
            "approval": approval,
            "interest_rate": interest_rate,
            "corrected_interest_rate": corrected_interest_rate,
            "tenure": tenure,
            "monthly_installment": monthly_installment
        }
    if loan_sanction_check:
        response["message"] = message
    return JsonResponse(response, status=status)


def sanction_loan(request):
    try:
        customer_id = request.POST.get("customer_id")
        loan_amount = request.POST.get("loan_amount")
        interest_rate = request.POST.get("interest_rate")
        tenure = request.POST.get("tenure")
        if customer_id!=None and loan_amount!=None and interest_rate!=None and tenure!=None and customer_id!="" and loan_amount!="" and interest_rate!="" and tenure!="":
            eligibility = check_eligibility(request, True)
            status_code = eligibility.status_code 
            eligibility = json.loads(eligibility.content.decode())
            loan_amount = int(loan_amount)
            tenure = int(tenure)
            interest_rate = eligibility["interest_rate"]
            if eligibility["approval"]:      
                x = {}
                x["Customer ID"] = customer_id
                x["Loan Amount"] = loan_amount
                x["Tenure"] = tenure
                x["Interest Rate"] = interest_rate
                x["Monthly payment"] = eligibility["monthly_installment"]
                x["EMIs paid on Time"] = 0
                loan_object = add_loan_data(x)
                if loan_object is not None:
                    loan_id = loan_object.loan_id
                    loan_approved = True
                    message = eligibility["message"]
                    emi = loan_object.emi
                    status = 201
                else:
                    loan_id = None
                    loan_approved = False
                    message = "Your loan was not created due to some internal error."
                    emi = None
                    status = 500
            elif status_code == 200:
                loan_id = None
                loan_approved = False
                message = eligibility["message"]
                emi = None
                status = 200
            elif status_code == 400 or status_code == 404 or status_code == 500:                
                loan_id = None
                loan_approved = False
                message = eligibility["message"]
                emi = None
                status = 200

        else:
            loan_id = None
            loan_approved = False
            message = "Your loan was not created due to missing/incorrect information."
            emi = None
            status = 400
    except Exception as e:
        loan_id = None
        loan_approved = False
        message = "Your loan was not created due to some internal error."
        emi = None
        status = 400

    response = {"loan_id": loan_id, 
                "customer_id": customer_id, 
                "loan_approved": loan_approved, 
                "messsage": message,
                "monthly_installment": emi
                }
    return JsonResponse(response, status=status)

