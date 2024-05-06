
from django.contrib import admin
from django.urls import path, include  # add this
from .views import HomeView,BookListView,BookCreateView,BookDeleteView,BookDetailView,BookUpdateView
from .views import CategoryListView,CategoryCreateView,CategoryDeleteView
from .views import PublisherListView,PublisherCreateView,PublisherDeleteView,PublisherUpdateView
from .views import ActivityListView,ActivityDeleteView
from .views import MemberCreateView,MemberUpdateView,MemberDeleteView,MemberListView,MemberDetailView
from .views import ProfileDetailView,ProfileCreateView,ProfileUpdateView
from django.conf import settings
from django.conf.urls.static import static
from .views import BorrowRecordListView,BorrowRecordCreateView,BorrowRecordDeleteView,BorrowRecordDetailView,auto_member,auto_book,BorrowRecordClose
from .views import DataCenterView,download_data,auto_user_name
from .views import ChartView,global_serach,EmployeeView,EmployeeDetailView,EmployeeUpdate,NoticeListView,NoticeUpdateView
from .views import TransactionListView,TransactionCreateView,TransactionDetailView, TransactionEditView
from .views import SavingsAccountListView, SavingsAccountCreateView, SavingsAccountDetailView, SavingsAccountUpdateView, SavingsAccountDeleteView
from .views import CheckingAccountListView, CheckingAccountCreateView, CheckingAccountDetailView, CheckingAccountUpdateView, CheckingAccountDeleteView
from .views import (
    HomeLoanListView, HomeLoanDetailView, HomeLoanCreateView, HomeLoanUpdateView, HomeLoanDeleteView,
    StudentLoanListView, StudentLoanDetailView, StudentLoanCreateView, StudentLoanUpdateView, StudentLoanDeleteView,
    LoanApplyView
)
from .views import HomePage, MonthlyTransactionView

urlpatterns = [

    # HomePage
    path("homepage",HomeView.as_view(), name='home'),
    path('',HomePage.as_view(), name='homepage'),
    # Book
    path('book-list',BookListView.as_view(),name="book_list"),
    path('book-create',BookCreateView.as_view(),name="book_create"),
    path('book-update/<int:pk>/',BookUpdateView.as_view(),name="book_update"),
    path('book-delete/<int:pk>/',BookDeleteView.as_view(),name="book_delete"),
    path('book-detail/<int:pk>/',BookDetailView.as_view(),name="book_detail"),

    # Category
    path('category-list',CategoryListView.as_view(),name="category_list"),
    path('category-create',CategoryCreateView.as_view(),name="category_create"),  
    path('category-delete/<int:pk>/',CategoryDeleteView.as_view(),name="category_delete"), 

    # Publisher
    path('publisher-list',PublisherListView.as_view(),name="publisher_list"),
    path('publisher-create',PublisherCreateView.as_view(),name="publisher_create"),  
    path('publisher-delete/<int:pk>/',PublisherDeleteView.as_view(),name="publisher_delete"), 
    path('publisher-update/<int:pk>/',PublisherUpdateView.as_view(),name="publisher_update"),

    # User Activity
    path('user-activity-list',ActivityListView.as_view(),name="user_activity_list"),
    path('user-activity-list/<int:pk>/',ActivityDeleteView.as_view(),name="user_activity_delete"),

    # Membership
    path('member-list',MemberListView.as_view(),name="member_list"),
    path('member-create',MemberCreateView.as_view(),name="member_create"),  
    path('member-delete/<int:pk>/',MemberDeleteView.as_view(),name="member_delete"), 
    path('member-update/<int:pk>/',MemberUpdateView.as_view(),name="member_update"),
    path('member-detail/<int:pk>/',MemberDetailView.as_view(),name="member_detail"),

    # UserProfile
    path('user/profile-create/',ProfileCreateView.as_view(),name="profile_create"),
    path('user/<int:pk>/profile/',ProfileDetailView.as_view(),name="profile_detail"),
    path('user/<int:pk>/profile-update/',ProfileUpdateView.as_view(),name="profile_update"),


    # BorrowRecords
    path('record-create/',BorrowRecordCreateView.as_view(),name="record_create"),
    path('record-create-autocomplete-member-name/',auto_member,name="auto_member_name"),
    path('record-create-autocomplete-book-name/',auto_book,name="auto_book_name"),
    path('record-list/',BorrowRecordListView.as_view(),name="record_list"),
    path('record-detail/<int:pk>/',BorrowRecordDetailView.as_view(),name="record_detail"),
    path('record-delete/<int:pk>/',BorrowRecordDeleteView.as_view(),name="record_delete"),
    path('record-close/<int:pk>/',BorrowRecordClose.as_view(),name="record_close"),

    # Data center
    path('data-center/',DataCenterView.as_view(),name="data_center"),
    path('data-download/<str:model_name>/',download_data,name="data_download"),

    # Chart
    path('charts/',ChartView.as_view(),name="chart"),
    path('monthly-transactions/', MonthlyTransactionView.as_view(), name='monthly-transactions'),
    # Global Search
    path('global-search/',global_serach,name="global_search"),

    # Employee
    path('employees/',EmployeeView.as_view(),name="employees_list"),
    path('employees-detail/<int:pk>',EmployeeDetailView.as_view(),name="employees_detail"),
    path('employees-update/<int:pk>',EmployeeUpdate,name='employee_update'),

    # Notice
    path('notice-list/', NoticeListView.as_view(), name='notice_list'),
    path('notice-update/', NoticeUpdateView.as_view(), name='notice_update'),

    # Transaction
    path('transactions-list/', TransactionListView.as_view(), name='transaction_list'),
    path('transaction/add/', TransactionCreateView.as_view(), name='transaction_add'),
    path('auto-user-name/', auto_user_name, name='auto_user_name'),
    path('transaction/<int:pk>/', TransactionDetailView.as_view(), name='transaction_detail'),
    path('transaction/edit/<int:pk>/', TransactionEditView.as_view(), name='transaction_edit'),

    # Savings Account
    path('savingsaccounts/', SavingsAccountListView.as_view(), name='savingsaccount_list'),
    path('savingsaccount/add/', SavingsAccountCreateView.as_view(), name='savingsaccount_create'),
    path('savingsaccount/<int:pk>/', SavingsAccountDetailView.as_view(), name='savingsaccount_detail'),
    path('savingsaccount/update/<int:pk>/', SavingsAccountUpdateView.as_view(), name='savingsaccount_update'),
    path('savingsaccount/delete/<int:pk>/', SavingsAccountDeleteView.as_view(), name='savingsaccount_delete'),

    # Checking Account
    path('checkingaccounts/', CheckingAccountListView.as_view(), name='checkingaccount_list'),
    path('checkingaccount/add/', CheckingAccountCreateView.as_view(), name='checkingaccount_create'),
    path('checkingaccount/<int:pk>/', CheckingAccountDetailView.as_view(), name='checkingaccount_detail'),
    path('checkingaccount/update/<int:pk>/', CheckingAccountUpdateView.as_view(), name='checkingaccount_update'),
    path('checkingaccount/delete/<int:pk>/', CheckingAccountDeleteView.as_view(), name='checkingaccount_delete'),

    # Loan
    path('home-loans/', HomeLoanListView.as_view(), name='home_loan_list'),
    path('home-loan/add/', HomeLoanCreateView.as_view(), name='home_loan_create'),
    path('home-loan/<int:pk>/', HomeLoanDetailView.as_view(), name='home_loan_detail'),
    path('home-loan/update/<int:pk>/', HomeLoanUpdateView.as_view(), name='home_loan_update'),
    path('home-loan/delete/<int:pk>/', HomeLoanDeleteView.as_view(), name='home_loan_delete'),

    path('student-loans/', StudentLoanListView.as_view(), name='student_loan_list'),
    path('student-loan/add/', StudentLoanCreateView.as_view(), name='student_loan_create'),
    path('student-loan/<int:pk>/', StudentLoanDetailView.as_view(), name='student_loan_detail'),
    path('student-loan/update/<int:pk>/', StudentLoanUpdateView.as_view(), name='student_loan_update'),
    path('student-loan/delete/<int:pk>/', StudentLoanDeleteView.as_view(), name='student_loan_delete'),

    path('apply-for-loan/', LoanApplyView.as_view(), name='loan_apply'),

]



