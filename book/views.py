import os
import pandas as pd
import json

from django.db.models.functions import ExtractMonth,ExtractWeek,TruncMonth,TruncWeek
from django.shortcuts import render,get_object_or_404,redirect
from django.urls import  reverse_lazy,reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView,DetailView,DeleteView,View,TemplateView
from django.views.generic.edit import CreateView,UpdateView
from django.core.paginator import Paginator
from django.db.models import Q,Sum
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from .models import Book,Category,Publisher,UserActivity,Profile,Member,BorrowRecord
from .models import Transaction, SavingsAccount, CheckingAccount, Loan, HomeLoan, StudentLoan
from django.apps import apps
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count
from django.contrib.auth.models import User,Group
from django.contrib.auth.decorators import login_required,user_passes_test
from django.utils.decorators import method_decorator
from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import messages
from .forms import BookCreateEditForm,PubCreateEditForm,MemberCreateEditForm,ProfileForm,BorrowRecordCreateForm
from .forms import TransactionForm, SavingsAccountForm, CheckingAccountForm,HomeLoanForm, StudentLoanForm
# from .utils import get_n_days_ago,create_clean_dir,change_col_format
from util.useful import get_n_days_ago
from .groups_permissions import check_user_group,user_groups,SuperUserRequiredMixin,allowed_groups
from datetime import date,timedelta
from django.utils.timezone import now
from django.core.paginator import Paginator
from comment.models import Comment
from comment.forms import CommentForm
from .notification import send_notification
import logging
from collections import OrderedDict


logger = logging.getLogger(__name__)



TODAY=get_n_days_ago(0,"%Y%m%d")
PAGINATOR_NUMBER = 5
allowed_models = ['Category','Publisher','Book','Member','UserActivity','BorrowRecord']



# HomePage

class HomeView(LoginRequiredMixin,TemplateView):
    login_url = 'login'
    template_name = "index.html"
    context={}

    def get(self, request, *args, **kwargs):

        book_count = Book.objects.aggregate(Sum('quantity'))['quantity__sum']

        data_count = {
            "book": book_count,
            "member": Member.objects.all().count(),
            "category": Category.objects.all().count(),
            "publisher": Publisher.objects.all().count(),
        }

        user_activities = UserActivity.objects.order_by("-created_at")[:5]
        user_avatar = {}
        for e in user_activities:
            try:
                profile = Profile.objects.get(user__username=e.created_by)
                user_avatar[e.created_by] = profile.profile_pic.url
            except Profile.DoesNotExist:
                user_avatar[e.created_by] = 'static/assets/images/user/avatar-1.jpg'  # 默认头像URL

        short_inventory = Book.objects.order_by('quantity')[:5]

        current_week = date.today().isocalendar()[1]
        new_members = Member.objects.order_by('-created_at')[:5]
        new_members_thisweek = Member.objects.filter(created_at__week=current_week).count()
        lent_books_thisweek = BorrowRecord.objects.filter(created_at__week=current_week).count()

        books_return_thisweek = BorrowRecord.objects.filter(end_day__week=current_week)
        number_books_return_thisweek = books_return_thisweek.count()
        new_closed_records = BorrowRecord.objects.filter(open_or_close=1).order_by('-closed_at')[:5]

        self.context['data_count'] = data_count
        self.context['recent_user_activities'] = user_activities
        self.context['user_avatar'] = user_avatar
        self.context['short_inventory'] = short_inventory
        self.context['new_members'] = new_members
        self.context['new_members_thisweek'] = new_members_thisweek
        self.context['lent_books_thisweek'] = lent_books_thisweek
        self.context['books_return_thisweek'] = books_return_thisweek
        self.context['number_books_return_thisweek'] = number_books_return_thisweek
        self.context['new_closed_records'] = new_closed_records

        return render(request, self.template_name, self.context)

class HomePage(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = "homepage.html"
    context = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 统计数据
        context['total_transaction_amount'] = round(Transaction.objects.aggregate(Sum('amount'))['amount__sum'],2) or 0
        context['total_savings_accounts'] = SavingsAccount.objects.count()
        context['total_checking_accounts'] = CheckingAccount.objects.count()
        context['transaction_count'] = Transaction.objects.count()

        # 获取最近的1条交易记录时间
        latest_transaction = Transaction.objects.order_by('-transaction_date').first()
        context['recent_transactions_date'] = latest_transaction.transaction_date.strftime("%Y-%m-%d") if latest_transaction else 'No Transactions'

        # 数据聚合
        saving_balances = SavingsAccount.objects.aggregate(total_balance=Sum('balance'))['total_balance'] or 0
        checking_balances = CheckingAccount.objects.aggregate(total_balance=Sum('balance'))['total_balance'] or 0
        context['total_balances'] = saving_balances + checking_balances
        # 活跃用户统计
        recent_transactions = Transaction.objects.filter(transaction_date__gte=now()-timedelta(days=30))
        context['active_users'] = recent_transactions.values('user').distinct().count()

        # 逾期贷款统计
        context['overdue_loans'] = Loan.objects.filter(due_date__lt=now(), status='overdue').aggregate(total_overdue=Sum('loan_amount'))

        # 最近的5笔交易记录
        recent_transactions_details = Transaction.objects.order_by('-transaction_date')[:5]
        context['recent_transactions'] = [{
            'user': trx.user.username,
            'amount': trx.account.account_number if trx.account else 'N/A',
            'transaction_type': trx.transaction_type,
            'date': trx.transaction_date.strftime("%Y-%m-%d"),
            'status': trx.status
        } for trx in recent_transactions_details]

        # 最近还款天数
        next_loan = Loan.objects.filter(status='active').order_by('due_date').first()
        context['days_until_repayment'] = next_loan.days_until_next_repayment() if next_loan else 'No Active Loans'

        #还款日剩余百分比
        context['days_until_repayment_percent'] = next_loan.days_until_next_repayment_percent() if next_loan else 'No Active Loans'

        return context

# Global Serch
@login_required(login_url='login')
def global_serach(request):
    search_value = request.POST.get('global_search')
    if search_value =='':
        return HttpResponseRedirect("/")

    r_category = Category.objects.filter(Q(name__icontains=search_value))
    r_publisher = Publisher.objects.filter(Q(name__icontains=search_value)|Q(contact__icontains=search_value))
    r_book = Book.objects.filter(Q(author__icontains=search_value)|Q(title__icontains=search_value))
    r_member = Member.objects.filter(Q(name__icontains=search_value)|Q(card_number__icontains=search_value)|Q(phone_number__icontains=search_value))
    r_borrow = BorrowRecord.objects.filter(Q(borrower__icontains=search_value)|Q(borrower_card__icontains=search_value)|Q(book__icontains=search_value))

   
    context={
        'categories':r_category,
        'publishers':r_publisher,
        'books':r_book,
        'members':r_member,
        'records':r_borrow,
    }

    return render(request, 'book/global_search.html',context=context)


# Chart
class ChartView(LoginRequiredMixin,TemplateView):
    template_name = "book/charts.html"
    login_url = 'login'
    context={}

    def get(self,request, *args, **kwargs):

        top_5_book= Book.objects.order_by('-quantity')[:5].values_list('title','quantity')
        top_5_book_titles = [b[0] for b in top_5_book ]
        top_5_book__quantities = [b[1] for b in top_5_book ]
        # print(top_5_book_titles,top_5_book__quantities)

        top_borrow = Book.objects.order_by('-total_borrow_times')[:5].values_list('title','total_borrow_times')
        top_borrow_titles = [b[0] for b in top_borrow ]
        top_borrow_times = [b[1] for b in top_borrow ]

        r_open = BorrowRecord.objects.filter(open_or_close=0).count()
        r_close = BorrowRecord.objects.filter(open_or_close=1).count()
        
        m = Member.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(c=Count('id'))
        months_member = [e['month'].strftime("%m/%Y") for e  in m]
        count_monthly_member= [e['c'] for e in m] 

       
        self.context['top_5_book_titles']=top_5_book_titles
        self.context['top_5_book__quantities']=top_5_book__quantities
        self.context['top_borrow_titles']=top_borrow_titles
        self.context['top_borrow_times']=top_borrow_times
        self.context['r_open']=r_open
        self.context['r_close']=r_close
        self.context['months_member']=months_member
        self.context['count_monthly_member']=count_monthly_member
       

        return render(request, self.template_name, self.context)


class MonthlyTransactionView(TemplateView):
    template_name = 'transactions/monthly_transactions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate the start date for the last five months
        end_date = now()
        start_date = end_date - relativedelta(months=4)  # Includes the current month and four previous months
        start_date = start_date.replace(
            day=1)  # Set to the first day of the start month to include all transactions from that month

        # Retrieve and process transactions
        transactions_by_month = (
            Transaction.objects.filter(transaction_date__gte=start_date)
            .annotate(month=TruncMonth('transaction_date'))
            .values('month')
            .annotate(total_amount=Sum('amount'), transaction_count=Count('id'))
            .order_by('month')
        )

        # Ensure all five months are represented in the data
        months = [start_date + relativedelta(months=i) for i in range(5)]
        totals_dict = OrderedDict((month.strftime('%Y-%m'), 0) for month in months)
        counts_dict = OrderedDict((month.strftime('%Y-%m'), 0) for month in months)

        for transaction in transactions_by_month:
            month_str = transaction['month'].strftime('%Y-%m')
            totals_dict[month_str] = float(transaction['total_amount'])
            counts_dict[month_str] = transaction['transaction_count']

        context['months'] = list(totals_dict.keys())
        context['totals'] = list(totals_dict.values())
        context['counts'] = list(counts_dict.values())

        return context

# Book
class BookListView(LoginRequiredMixin,ListView):
    login_url = 'login'
    model=Book
    context_object_name = 'books'
    template_name = 'book/book_list.html'
    search_value=""
    order_field="-updated_at"

    def get_queryset(self):
        search =self.request.GET.get("search") 
        order_by=self.request.GET.get("orderby")

        if order_by:
            all_books = Book.objects.all().order_by(order_by)
            self.order_field=order_by
        else:
            all_books = Book.objects.all().order_by(self.order_field)

        if search:
            all_books = all_books.filter(
                Q(title__icontains=search)|Q(author__icontains=search)
            )
            self.search_value=search
        self.count_total = all_books.count()
        paginator = Paginator(all_books, PAGINATOR_NUMBER)
        page = self.request.GET.get('page')
        books = paginator.get_page(page)
        return books

    def get_context_data(self, *args, **kwargs):
        context = super(BookListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        context['orderby'] = self.order_field
        context['objects'] = self.get_queryset()
        return context

class BookDetailView(LoginRequiredMixin,DetailView):
    model = Book
    context_object_name = 'book'
    template_name = 'book/book_detail.html'
    login_url = 'login'
    comment_form = CommentForm()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_book_name = self.get_object().title
        logger.info(f'Book  <<{current_book_name}>> retrieved from db')
        comments = Comment.objects.filter(book=self.get_object().id)
        related_records = BorrowRecord.objects.filter(book=current_book_name)
        context['related_records'] = related_records
        context['comments'] = comments
        context['comment_form'] = self.comment_form
        return context

class BookCreateView(LoginRequiredMixin,CreateView):
    model=Book
    login_url = 'login'
    form_class=BookCreateEditForm    
    template_name='book/book_create.html'

    def post(self,request, *args, **kwargs):
        super(BookCreateView,self).post(request)
        new_book_name = request.POST['title']
        messages.success(request, f"New Book << {new_book_name} >> Added")
        UserActivity.objects.create(created_by=self.request.user.username,
                                    target_model=self.model.__name__,
                                    detail =f"Create {self.model.__name__} << {new_book_name} >>")
        return redirect('book_list')

class BookUpdateView(LoginRequiredMixin,UpdateView):
    model = Book
    login_url = 'login'
    form_class=BookCreateEditForm
    template_name = 'book/book_update.html'

    def post(self, request, *args, **kwargs):
        current_book = self.get_object()
        current_book.updated_by=self.request.user.username
        current_book.save(update_fields=['updated_by'])
        UserActivity.objects.create(created_by=self.request.user.username,
            operation_type="warning",
            target_model=self.model.__name__,
            detail =f"Update {self.model.__name__} << {current_book.title} >>")
        return super(BookUpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
      title=form.cleaned_data['title']      
      messages.warning(self.request, f"Update << {title} >> success")
      return super().form_valid(form)

class BookDeleteView(LoginRequiredMixin,View):
    login_url = 'login'
    def get(self,request,*args,**kwargs):
        book_pk=kwargs["pk"]
        delete_book=Book.objects.get(pk=book_pk)
        model_name = delete_book.__class__.__name__
        messages.error(request, f"Book << {delete_book.title} >> Removed")
        delete_book.delete()
        UserActivity.objects.create(created_by=self.request.user.username,
            operation_type="danger",
            target_model=model_name,
            detail =f"Delete {model_name} << {delete_book.title} >>")
        return HttpResponseRedirect(reverse("book_list"))

# Categorty

class CategoryListView(LoginRequiredMixin,ListView):
    login_url = 'login'
    model=Category
    context_object_name = 'categories'
    template_name = 'book/category_list.html'
    count_total = 0
    search_value = ''
    order_field="-created_at"


    def get_queryset(self):
        search =self.request.GET.get("search")  
        order_by=self.request.GET.get("orderby")
        if order_by:
            all_categories = Category.objects.all().order_by(order_by)
            self.order_field=order_by
        else:
            all_categories = Category.objects.all().order_by(self.order_field)
        if search:
            all_categories = all_categories.filter(
                Q(name__icontains=search)  
            )
            self.search_value=search

        self.count_total = all_categories.count()
        paginator = Paginator(all_categories, PAGINATOR_NUMBER)
        page = self.request.GET.get('page')
        categories = paginator.get_page(page)
        return categories

    def get_context_data(self, *args, **kwargs):
        context = super(CategoryListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        context['orderby'] = self.order_field
        context['objects'] = self.get_queryset()
        return context

class CategoryCreateView(LoginRequiredMixin,CreateView):
    login_url = 'login'
    model=Category
    fields=['name']
    template_name='book/category_create.html'
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        new_cat = form.save(commit=False)
        new_cat.save()
        send_notification(self.request.user,new_cat,verb=f'Add New Category << {new_cat.name} >>')
        logger.info(f'{self.request.user} created Category {new_cat.name}')
        UserActivity.objects.create(created_by=self.request.user.username,
                                    target_model=self.model.__name__,
                                    detail =f"Create {self.model.__name__} << {new_cat.name} >>")
        return super(CategoryCreateView, self).form_valid(form)



class CategoryDeleteView(LoginRequiredMixin,View):
    login_url = 'login'

    def get(self,request,*args,**kwargs):
        cat_pk=kwargs["pk"]
        delete_cat=Category.objects.get(pk=cat_pk)
        model_name = delete_cat.__class__.__name__
        messages.error(request, f"Category << {delete_cat.name} >> Removed")
        delete_cat.delete()
        send_notification(self.request.user,delete_cat,verb=f'Delete Category << {delete_cat.name} >>')
        UserActivity.objects.create(created_by=self.request.user.username,
                            operation_type="danger",
                            target_model=model_name,
                            detail =f"Delete {model_name} << {delete_cat.name} >>")

        logger.info(f'{self.request.user} delete Category {delete_cat.name}')

        return HttpResponseRedirect(reverse("category_list"))


# Publisher 

class PublisherListView(LoginRequiredMixin,ListView):
    login_url = 'login'
    model=Publisher
    context_object_name = 'publishers'
    template_name = 'book/publisher_list.html'
    count_total = 0
    search_value = ''
    order_field="-created_at"

    def get_queryset(self):
        search =self.request.GET.get("search")  
        order_by=self.request.GET.get("orderby")
        if order_by:
            all_publishers = Publisher.objects.all().order_by(order_by)
            self.order_field=order_by
        else:
            all_publishers = Publisher.objects.all().order_by(self.order_field)
        if search:
            all_publishers = all_publishers.filter(
                Q(name__icontains=search) | Q(city__icontains=search) | Q(contact__icontains=search)
            )
        else:
            search = ''
        self.search_value=search
        self.count_total = all_publishers.count()
        paginator = Paginator(all_publishers, PAGINATOR_NUMBER)
        page = self.request.GET.get('page')
        publishers = paginator.get_page(page)
        return publishers

    def get_context_data(self, *args, **kwargs):
        context = super(PublisherListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        context['orderby'] = self.order_field  
        context['objects'] = self.get_queryset()      
        return context

class PublisherCreateView(LoginRequiredMixin,CreateView):
    model=Publisher
    login_url = 'login'
    form_class=PubCreateEditForm
    template_name='book/publisher_create.html'
    success_url = reverse_lazy('publisher_list')


    def form_valid(self,form):
        new_pub = form.save(commit=False)
        new_pub.save()
        messages.success(self.request, f"New Publisher << {new_pub.name} >> Added")
        send_notification(self.request.user,new_pub,verb=f'Add New Publisher << {new_pub.name} >>')
        logger.info(f'{self.request.user} created Publisher {new_pub.name}')

        UserActivity.objects.create(created_by=self.request.user.username,
                                    target_model=self.model.__name__,
                                    detail =f"Create {self.model.__name__} << {new_pub.name} >>")
        return super(PublisherCreateView, self).form_valid(form)


class PublisherUpdateView(LoginRequiredMixin,UpdateView):
    model=Publisher
    login_url = 'login'
    form_class=PubCreateEditForm
    template_name = 'book/publisher_update.html'

    def post(self, request, *args, **kwargs):
        current_pub = self.get_object()
        current_pub.updated_by=self.request.user.username
        current_pub.save(update_fields=['updated_by'])
        UserActivity.objects.create(created_by=self.request.user.username,
                                    operation_type="warning",
                                    target_model=self.model.__name__,
                                    detail =f"Update {self.model.__name__} << {current_pub.name} >>")
        return super(PublisherUpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        title=form.cleaned_data['name']      
        messages.warning(self.request, f"Update << {title} >> success")
        return super().form_valid(form)

class PublisherDeleteView(LoginRequiredMixin,View):
    login_url = 'login'

    def get(self,request,*args,**kwargs):
        pub_pk=kwargs["pk"]
        delete_pub=Publisher.objects.get(pk=pub_pk)
        model_name = delete_pub.__class__.__name__
        messages.error(request, f"Publisher << {delete_pub.name} >> Removed")
        delete_pub.delete()
        send_notification(self.request.user,delete_pub,verb=f'Delete Publisher << {delete_pub.name} >>')
        logger.info(f'{self.request.user} delete Publisher {delete_pub.name}')
        UserActivity.objects.create(created_by=self.request.user.username,
                    operation_type="danger",
                    target_model=model_name,
                    detail =f"Delete {model_name} << {delete_pub.name} >>")
        return HttpResponseRedirect(reverse("publisher_list"))


# User Logs  
# @method_decorator(user_passes_test(lambda u: u.has_perm("book.view_useractivity")), name='dispatch')
@method_decorator(allowed_groups(group_name=['logs']), name='dispatch')
class ActivityListView(LoginRequiredMixin,ListView):

    login_url = 'login'
    model= UserActivity
    context_object_name = 'activities'
    template_name = 'book/user_activity_list.html'
    count_total = 0
    search_value=''
    created_by=''
    order_field="-created_at"
    all_users = User.objects.values()
    user_list = [x['username'] for x in all_users] 

    # def dispatch(self, *args, **kwargs):
    #     return super(ActivityListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        data = self.request.GET.copy()
        search =self.request.GET.get("search")
        filter_user=self.request.GET.get("created_by") 

        all_activities = UserActivity.objects.all()

        if filter_user:
            self.created_by = filter_user
            all_activities = all_activities.filter(created_by=self.created_by)

        if search:
            self.search_value = search
            all_activities = all_activities.filter(Q(target_model__icontains=search))

        self.search_value=search
        self.count_total = all_activities.count()
        paginator = Paginator(all_activities,PAGINATOR_NUMBER)
        page = self.request.GET.get('page')
        try:
            response = paginator.get_page(page)
        except PageNotAnInteger:
            response = paginator.get_page(1)
        except EmptyPage:
            response = paginator.get_page(paginator.num_pages)
        return response

    
    def get_context_data(self, *args, **kwargs):
        context = super(ActivityListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        context['user_list']= self.user_list
        context['created_by'] = self.created_by
        return context


# @method_decorator(user_passes_test(lambda u: u.has_perm("book.delete_useractivity")), name='dispatch')
@method_decorator(allowed_groups(group_name=['logs']), name='dispatch')
class ActivityDeleteView(LoginRequiredMixin,View):

    login_url = 'login'

    def get(self,request,*args,**kwargs):
        
        log_pk=kwargs["pk"]
        delete_log=UserActivity.objects.get(pk=log_pk)
        messages.error(request, f"Activity Removed")
        delete_log.delete()

        return HttpResponseRedirect(reverse("user_activity_list"))


# Membership
class MemberListView(LoginRequiredMixin,ListView):
    login_url = 'login'
    model= Member
    context_object_name = 'members'
    template_name = 'book/member_list.html'
    count_total = 0
    search_value = ''
    order_field="-updated_at"

    def get_queryset(self):
        search =self.request.GET.get("search")  
        order_by=self.request.GET.get("orderby")
        if order_by:
            all_members = Member.objects.all().order_by(order_by)
            self.order_field=order_by
        else:
            all_members = Member.objects.all().order_by(self.order_field)
        if search:
            all_members = all_members.filter(
                Q(name__icontains=search) |  Q(card_number__icontains=search)
            )
        else:
            search = ''
        self.search_value=search
        self.count_total = all_members.count()
        paginator = Paginator(all_members, PAGINATOR_NUMBER)
        page = self.request.GET.get('page')
        members = paginator.get_page(page)
        return members

    def get_context_data(self, *args, **kwargs):
        context = super(MemberListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        context['orderby'] = self.order_field
        context['objects'] = self.get_queryset()
        return context

class MemberCreateView(LoginRequiredMixin,CreateView):
    model=Member
    login_url = 'login'
    form_class=MemberCreateEditForm
    template_name='book/member_create.html'

    def post(self,request, *args, **kwargs):
        super(MemberCreateView,self).post(request)
        new_member_name = request.POST['name']
        messages.success(request, f"New Member << {new_member_name} >> Added")
        UserActivity.objects.create(created_by=self.request.user.username,
                                    target_model=self.model.__name__,
                                    detail =f"Create {self.model.__name__} << {new_member_name} >>")
        return redirect('member_list')

    def form_valid(self, form):
        self.object = form.save()
        self.object.created_by = self.request.user.username
        self.object.save(update_fields=['created_by'])
        send_notification(self.request.user,self.object,f'Add new memeber {self.object.name}')
    
        return HttpResponseRedirect(self.get_success_url())



class MemberUpdateView(LoginRequiredMixin,UpdateView):
    model = Member
    login_url = 'login'
    form_class=MemberCreateEditForm
    template_name = 'book/member_update.html'

    def post(self, request, *args, **kwargs):
        current_member = self.get_object()
        current_member.updated_by=self.request.user.username
        current_member.save(update_fields=['updated_by'])
        UserActivity.objects.create(created_by=self.request.user.username,
            operation_type="warning",
            target_model=self.model.__name__,
            detail =f"Update {self.model.__name__} << {current_member.name} >>")
        return super(MemberUpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        member_name=form.cleaned_data['name']      
        messages.warning(self.request, f"Update << {member_name} >> success")
        return super().form_valid(form)

class MemberDeleteView(LoginRequiredMixin,View):
    login_url = 'login'

    def get(self,request,*args,**kwargs):
        member_pk=kwargs["pk"]
        delete_member=Member.objects.get(pk=member_pk)
        model_name = delete_member.__class__.__name__
        messages.error(request, f"Member << {delete_member.name} >> Removed")
        delete_member.delete()
        send_notification(self.request.user,delete_member,f'Delete member {delete_member.name} ')


        UserActivity.objects.create(created_by=self.request.user.username,
                    operation_type="danger",
                    target_model=model_name,
                    detail =f"Delete {model_name} << {delete_member.name} >>")
        return HttpResponseRedirect(reverse("member_list"))

class MemberDetailView(LoginRequiredMixin,DetailView):
    model = Member
    context_object_name = 'member'
    template_name = 'book/member_detail.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_member_name = self.get_object().name
        related_records = BorrowRecord.objects.filter(borrower=current_member_name)
        context['related_records'] = related_records
        context["card_number"] = str(self.get_object().card_id)[:8]
        return context


# Profile View

class ProfileDetailView(LoginRequiredMixin,DetailView):
    model = Profile
    context_object_name = 'profile'
    template_name = 'profile/profile_detail.html'
    login_url = 'login'


    def get_context_data(self, *args, **kwargs):
        current_user= get_object_or_404(Profile,pk=self.kwargs['pk'])
        # current_user= Profile.get(pk=kwargs['pk'])
        context = super(ProfileDetailView, self).get_context_data(*args, **kwargs)
        context['current_user'] = current_user
        return context

class ProfileCreateView(LoginRequiredMixin,CreateView):
    model = Profile
    template_name = 'profile/profile_create.html'
    login_url = 'login'
    form_class= ProfileForm

    def form_valid(self,form) -> HttpResponse:
        form.instance.user = self.request.user
        return super().form_valid(form)

class ProfileUpdateView(LoginRequiredMixin,UpdateView):
    model = Profile
    login_url = 'login'
    form_class=ProfileForm
    template_name = 'profile/profile_update.html'

# Borrow Records 

class BorrowRecordCreateView(LoginRequiredMixin,CreateView):
    model = BorrowRecord
    template_name = 'borrow_records/create.html'
    form_class=BorrowRecordCreateForm
    login_url = 'login'

    

    def get_form(self):
        form = super().get_form()
        return form

    def form_valid(self, form):
        selected_member= get_object_or_404(Member,name = form.cleaned_data['borrower'] )
        selected_book = Book.objects.get(title=form.cleaned_data['book'])

        form.instance.borrower_card = selected_member.card_number
        form.instance.borrower_email = selected_member.email
        form.instance.borrower_phone_number = selected_member.phone_number
        form.instance.created_by = self.request.user.username
        form.instance.start_day = form.cleaned_data['start_day']
        form.instance.end_day = form.cleaned_data['end_day']
        form.save()


        # Change field on Model Book
        selected_book.status=0
        selected_book.total_borrow_times+=1
        selected_book.quantity-=int(form.cleaned_data['quantity'])
        selected_book.save()

        # Create Log 
        borrower_name = selected_member.name
        book_name = selected_book.title

        messages.success(self.request, f" '{borrower_name}' borrowed <<{book_name}>>")
        UserActivity.objects.create(created_by=self.request.user.username,
                                    target_model=self.model.__name__,
                                    detail =f" '{borrower_name}' borrowed <<{book_name}>>")


        return super(BorrowRecordCreateView,self).form_valid(form)




@login_required(login_url='login')
def auto_member(request):
    if request.is_ajax():
        query = request.GET.get("term", "")
        member_names = Member.objects.filter(name__icontains=query)
        results = []
        for m in member_names:
            results.append(m.name)
        data = json.dumps(results)
    mimetype = "application/json"
    return HttpResponse(data, mimetype)

@login_required(login_url='login')
def auto_book(request):
    if request.is_ajax():
        query = request.GET.get("term", "")
        book_names = Book.objects.filter(title__icontains=query)
        results = [b.title for b in book_names]
        data = json.dumps(results)
    mimetype = "application/json"
    return HttpResponse(data, mimetype)

class BorrowRecordDetailView(LoginRequiredMixin,DetailView):
    model = BorrowRecord
    context_object_name = 'record'
    template_name = 'borrow_records/detail.html'
    login_url = 'login'   

    def get_context_data(self, **kwargs):
        context = super(BorrowRecordDetailView, self).get_context_data(**kwargs)
        related_member = Member.objects.get(name=self.get_object().borrower)
        context['related_member'] = related_member
        return context

class BorrowRecordListView(LoginRequiredMixin,ListView):
    model = BorrowRecord  # model name
    template_name = 'borrow_records/list.html'  # template name
    login_url = 'login'
    context_object_name = 'records'
    count_total = 0
    search_value = ''
    order_field="-closed_at"

    def get_queryset(self):
        search =self.request.GET.get("search")  
        order_by=self.request.GET.get("orderby")
        if order_by:
            all_records = BorrowRecord.objects.all().order_by(order_by)
            self.order_field=order_by
        else:
            all_records = BorrowRecord.objects.all().order_by(self.order_field)
        if search:
            all_records = BorrowRecord.objects.filter(
                Q(borrower__icontains=search) | Q(book__icontains=search) | Q(borrower_card__icontains=search)
            )
        else:
            search = ''
        self.search_value=search
        self.count_total = all_records.count()
        paginator = Paginator(all_records, PAGINATOR_NUMBER)
        page = self.request.GET.get('page')
        records = paginator.get_page(page)
        return records

    def get_context_data(self, *args, **kwargs):
        context = super(BorrowRecordListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        context['orderby'] = self.order_field
        context['objects'] = self.get_queryset()
        return context

class BorrowRecordDeleteView(LoginRequiredMixin,View):
    login_url = 'login'

    def get(self,request,*args,**kwargs):
        record_pk=kwargs["pk"]
        delete_record=BorrowRecord.objects.get(pk=record_pk)
        model_name = delete_record.__class__.__name__
        messages.error(request, f"Record {delete_record.borrower} => {delete_record.book} Removed")
        delete_record.delete()
        UserActivity.objects.create(created_by=self.request.user.username,
                    operation_type="danger",
                    target_model=model_name,
                    detail =f"Delete {model_name} {delete_record.borrower}")
        return HttpResponseRedirect(reverse("record_list"))

class BorrowRecordClose(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):

        close_record = BorrowRecord.objects.get(pk=self.kwargs['pk'])
        close_record.closed_by = self.request.user.username
        close_record.final_status = close_record.return_status
        close_record.delay_days = close_record.get_delay_number_days
        close_record.open_or_close = 1
        close_record.save()
        print(close_record.open_or_close,close_record.final_status,close_record.pk)
        

        borrowed_book = Book.objects.get(title=close_record.book)
        borrowed_book.quantity+=1
        count_record_same_book = BorrowRecord.objects.filter(book=close_record.book).count()
        if count_record_same_book==1:
            borrowed_book.status = 1

        borrowed_book.save()

        model_name = close_record.__class__.__name__
        UserActivity.objects.create(created_by=self.request.user.username,
                    operation_type="info",
                    target_model=model_name,
                    detail =f"Close {model_name} '{close_record.borrower}'=>{close_record.book}")
        return HttpResponseRedirect(reverse("record_list"))


# Data center
@method_decorator(allowed_groups(group_name=['download_data']), name='dispatch')
class DataCenterView(LoginRequiredMixin,TemplateView):
    template_name = 'book/download_data.html'
    login_url = 'login'

    def get(self,request,*args, **kwargs):
        # check_user_group(request.user,"download_data")
        data = {m.objects.model._meta.db_table:
        {"source":pd.DataFrame(list(m.objects.all().values())) ,
          "path":f"{str(settings.BASE_DIR)}/datacenter/{m.__name__}_{TODAY}.csv",
           "file_name":f"{m.__name__}_{TODAY}.csv"} for m in apps.get_models() if m.__name__ in allowed_models}
        
        count_total = {k: v['source'].shape[0] for k,v in data.items()}
        return render(request,self.template_name,context={'model_list':count_total})

@login_required(login_url='login')
@allowed_groups(group_name=['download_data'])
def download_data(request,model_name):
    check_user_group(request.user,"download_data")
            
    download = {m.objects.model._meta.db_table:
        {"source":pd.DataFrame(list(m.objects.all().values())) ,
          "path":f"{str(settings.BASE_DIR)}/datacenter/{m.__name__}_{TODAY}.csv",
           "file_name":f"{m.__name__}_{TODAY}.csv"} for m in apps.get_models() if m.__name__ in allowed_models}

    download[model_name]['source'].to_csv(download[model_name]['path'],index=False,encoding='utf-8')
    download_file=pd.read_csv(download[model_name]['path'],encoding='utf-8')
    response = HttpResponse(download_file,content_type="text/csv")
    response = HttpResponse(open(download[model_name]['path'],'r',encoding='utf-8'),content_type="text/csv")
    response['Content-Disposition'] = f"attachment;filename={download[model_name]['file_name']}"
    return response


    
# Handle Errors

def page_not_found(request, exception):
    context = {}
    response = render(request, "errors/404.html", context=context)
    response.status_code = 404
    return response
    
def server_error(request, exception=None):
    context = {}
    response = render(request, "errors/500.html", context=context)
    response.status_code = 500
    return response
    
def permission_denied(request, exception=None):
    context = {}
    response = render(request, "errors/403.html", context=context)
    response.status_code = 403
    return response
    
def bad_request(request, exception=None):
    context = {}
    response = render(request, "errors/400.html", context=context)
    response.status_code = 400
    return response


class EmployeeView(SuperUserRequiredMixin,ListView):
    login_url = 'login'
    model=User
    context_object_name = 'employees'
    template_name = 'book/employees.html'


class EmployeeDetailView(SuperUserRequiredMixin,DetailView):
    model = User
    context_object_name = 'employee'
    template_name = 'book/employee_detail.html'
    login_url = 'login'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = user_groups
        return context


@user_passes_test(lambda u: u.is_superuser)
@login_required(login_url='login')
def EmployeeUpdate(request,pk):
    # check_superuser(request.user)
    current_user = User.objects.get(pk=pk)
    if request.method == 'POST':
        chosen_groups = [ g for g in user_groups if "on" in request.POST.getlist(g)]
        current_user.groups.clear()
        for each in chosen_groups:
            group = Group.objects.get(name=each)
            current_user.groups.add(group)
        messages.success(request, f"Group for  << {current_user.username} >> has been updated")
        return redirect('employees_detail', pk=pk)



# Notice

class NoticeListView(SuperUserRequiredMixin, ListView):
    context_object_name = 'notices'
    template_name = 'notice_list.html'
    login_url = 'login'

    # 未读通知的查询集
    def get_queryset(self):
        return self.request.user.notifications.unread()


class NoticeUpdateView(SuperUserRequiredMixin,View):
    """Update Status of Notification"""
    # 处理 get 请求
    def get(self, request):
        # 获取未读消息
        notice_id = request.GET.get('notice_id')
        # 更新单条通知
        if notice_id:
            request.user.notifications.get(id=notice_id).mark_as_read()
            return redirect('category_list')
        # 更新全部通知
        else:
            request.user.notifications.mark_all_as_read()
            return redirect('notice_list')

# --------
class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction  # Using the Transaction model
    template_name = 'transactions/transaction_list.html'  # Assuming you have this template
    login_url = 'login'  # Redirects to login page if user is not authenticated
    context_object_name = 'transactions'
    paginate_by = 10  # Or any other number that suits your design

    def get_queryset(self):
        """
        Overriding the queryset to include custom filtering and ordering based on query parameters.
        """
        search = self.request.GET.get("search", "")
        order_by = self.request.GET.get("orderby", "-transaction_date")  # Default ordering

        queryset = Transaction.objects.all().order_by(order_by)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(description__icontains=search) |
                Q(transaction_type__icontains=search) |
                Q(payment_method__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        """
        Overriding context data to include search and order fields in the template context.
        """
        context = super().get_context_data(**kwargs)
        context['search_value'] = self.request.GET.get("search", "")
        context['order_field'] = self.request.GET.get("orderby", "-transaction_date")
        context['count_total'] = self.get_queryset().count()
        return context

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    template_name = 'transactions/create.html'
    form_class = TransactionForm
    login_url = 'login'
    success_url = reverse_lazy('transaction_list')  # 确保定义了跳转的URL

    def get_form_kwargs(self):
        kwargs = super(TransactionCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user  # 传递当前登录的用户实例
        return kwargs

    def form_valid(self, form):
        transaction = form.save(commit=False)
        transaction.user = self.request.user  # Link the transaction to the logged-in user
        account = form.cleaned_data['account']  # Directly use the account selected in the form
        if not account:
            messages.error(self.request, "No account found for transaction.")
            return self.form_invalid(form)

        # Handle balance updates based on account and transaction type
        try:
            account.update_balance(transaction.amount, transaction.transaction_type)
            transaction.save()
            messages.success(self.request, f"Transaction '{transaction.transaction_type}' of amount {transaction.amount} was successful.")
            # return redirect('transaction_list')
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

        return super().form_valid(form)

class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    context_object_name = 'transaction'
    template_name = 'transactions/detail.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_transaction = self.get_object()
        logger.info(f'Transaction ID <<{current_transaction.id}>> accessed')

        return context

class TransactionEditView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/edit_transaction.html'
    login_url = 'login'
    success_url = reverse_lazy('transaction_list')  # Redirect to the transaction list after successful update

    def form_valid(self, form):
        # Custom logic can be added here
        transaction = form.save(commit=False)
        transaction.user = self.request.user  # Link the transaction to the logged-in user
        account = form.cleaned_data['account']  # Directly use the account selected in the form
        if not account:
            messages.error(self.request, "No account found for transaction.")
            return self.form_invalid(form)

        # Handle balance updates based on account and transaction type
        try:
            account.update_balance(transaction.amount, transaction.transaction_type)
            transaction.save()
            messages.success(self.request, f"Transaction '{transaction.transaction_type}' of amount {transaction.amount} was successful.")
            # return redirect('transaction_list')
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

        messages.success(self.request, "Transaction updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Custom handling of invalid form submissions
        messages.error(self.request, "Error updating the transaction. Please check the form data.")
        return super().form_invalid(form)
def auto_user_name(request):
    term = request.GET.get('term')  # jQuery UI sends the term as 'term'
    if term:
        users = User.objects.filter(username__icontains=term, is_active=True).order_by('username')[:10]  # Limit to 10 results
        usernames = list(users.values_list('username', flat=True))
        return JsonResponse(usernames, safe=False)
    return JsonResponse([])


class SavingsAccountListView(LoginRequiredMixin, ListView):
    model = SavingsAccount
    template_name = 'savingsaccount/savingsaccount_list.html'
    context_object_name = 'savings_accounts'
    paginate_by = 10  # Number of accounts per page
    login_url = 'login'

    def get_queryset(self):
        search = self.request.GET.get("search", "")
        order_by = self.request.GET.get("orderby", "-created_at")

        queryset = SavingsAccount.objects.all().order_by(order_by)
        if search:
            queryset = queryset.filter(
                Q(owner__username__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_value': self.request.GET.get("search", ""),
            'order_field': self.request.GET.get("orderby", "-created_at")
        })
        return context

class SavingsAccountDetailView(LoginRequiredMixin, DetailView):
    model = SavingsAccount
    template_name = 'savingsaccount/savingsaccount_detail.html'
    context_object_name = 'account'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['savingsaccount'] = self.get_object()
        return context

class SavingsAccountCreateView(LoginRequiredMixin, CreateView):
    model = SavingsAccount
    form_class = SavingsAccountForm
    template_name = 'savingsaccount/savingsaccount_form.html'
    login_url = 'login'
    success_url = reverse_lazy('savingsaccount_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Set the owner to the current user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['button_text'] = 'Create Account'  # Set the text for create
        context['view_title'] = 'Create New Savings Account'
        context['header_title'] = 'Enter Account Details'
        return context

class SavingsAccountUpdateView(LoginRequiredMixin, UpdateView):
    model = SavingsAccount
    form_class = SavingsAccountForm
    template_name = 'savingsaccount/savingsaccount_form.html'
    login_url = 'login'
    success_url = reverse_lazy('savingsaccount_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['button_text'] = 'Update Account'  # Set the text for update
        context['view_title'] = 'Update Savings Account'
        context['header_title'] = 'Modify Account Details'
        return context

class SavingsAccountDeleteView(LoginRequiredMixin, DeleteView):
    model = SavingsAccount
    template_name = 'savingsaccount/savingsaccount_confirm_delete.html'
    login_url = 'login'
    success_url = reverse_lazy('savingsaccount_list')

# Checking Account
class CheckingAccountListView(LoginRequiredMixin, ListView):
    model = CheckingAccount
    template_name = 'checkingaccount/checkingaccount_list.html'
    context_object_name = 'checking_accounts'
    paginate_by = 10  # Number of accounts per page
    login_url = 'login'

    def get_queryset(self):
        search = self.request.GET.get("search", "")
        order_by = self.request.GET.get("orderby", "-created_at")

        queryset = CheckingAccount.objects.all().order_by(order_by)
        if search:
            queryset = queryset.filter(
                Q(owner__username__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_value': self.request.GET.get("search", ""),
            'order_field': self.request.GET.get("orderby", "-created_at")
        })
        return context

class CheckingAccountDetailView(LoginRequiredMixin, DetailView):
    model = CheckingAccount
    template_name = 'checkingaccount/checkingaccount_detail.html'
    context_object_name = 'account'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['checkingaccount'] = self.get_object()
        return context

class CheckingAccountCreateView(LoginRequiredMixin, CreateView):
    model = CheckingAccount
    form_class = CheckingAccountForm
    template_name = 'checkingaccount/checkingaccount_form.html'
    login_url = 'login'
    success_url = reverse_lazy('checkingaccount_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Automatically set the owner to the current user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['button_text'] = 'Create Account'  # Set the text for create
        context['view_title'] = 'Create New Checking Account'
        context['header_title'] = 'Enter Account Details'
        return context

class CheckingAccountUpdateView(LoginRequiredMixin, UpdateView):
    model = CheckingAccount
    form_class = CheckingAccountForm
    template_name = 'checkingaccount/checkingaccount_form.html'
    login_url = 'login'
    success_url = reverse_lazy('checkingaccount_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['button_text'] = 'Update Account'  # Set the text for update
        context['view_title'] = 'Update Checking Account'
        context['header_title'] = 'Modify Account Details'
        return context

class CheckingAccountDeleteView(LoginRequiredMixin, DeleteView):
    model = CheckingAccount
    template_name = 'checkingaccount/checkingaccount_confirm_delete.html'
    login_url = 'login'
    success_url = reverse_lazy('checkingaccount_list')

# Loan Management
class LoanApplyView(LoginRequiredMixin, CreateView):
    template_name = 'loans/loan_apply_form.html'
    form_class = HomeLoanForm  # Default to HomeLoan, change as per your logic
    login_url = 'login'
    success_url = reverse_lazy('loan_list')

    def get_form_class(self):
        # This method can be overridden to return different forms based on the request, such as query parameters
        return super().get_form_class()

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class HomeLoanListView(LoginRequiredMixin, ListView):
    model = HomeLoan
    template_name = 'loans/home_loan_list.html'
    context_object_name = 'loans'
    login_url = 'login'
    paginate_by = 10

class HomeLoanDetailView(LoginRequiredMixin, DetailView):
    model = HomeLoan
    template_name = 'loans/home_loan_detail.html'
    context_object_name = 'home_loan'
    login_url = 'login'

class HomeLoanCreateView(LoginRequiredMixin, CreateView):
    model = HomeLoan
    form_class = HomeLoanForm
    template_name = 'loans/home_loan_form.html'
    login_url = 'login'
    success_url = reverse_lazy('home_loan_list')

    def form_valid(self, form):
        # Calculate the due date from the start_date and loan_term before saving
        # Set the owner to the current user before saving the form
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_title'] = 'Home Loan Application'
        context['header_title'] = 'Apply for a New Home Loan'
        context['button_text'] = 'Submit Application'
        return context

class HomeLoanUpdateView(LoginRequiredMixin, UpdateView):
    model = HomeLoan
    form_class = HomeLoanForm
    template_name = 'loans/home_loan_form.html'
    login_url = 'login'
    success_url = reverse_lazy('home_loan_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_title'] = 'Update Home Loan Application'
        context['header_title'] = 'Update Your Home Loan'
        context['button_text'] = 'Modify Loan Details'
        return context

class HomeLoanDeleteView(LoginRequiredMixin, DeleteView):
    model = HomeLoan
    template_name = 'loans/home_loan_confirm_delete.html'
    login_url = 'login'
    success_url = reverse_lazy('home_loan_list')

class StudentLoanListView(LoginRequiredMixin, ListView):
    model = StudentLoan
    template_name = 'loans/student_loan_list.html'
    context_object_name = 'student_loans'
    login_url = 'login'
    paginate_by = 10

class StudentLoanDetailView(LoginRequiredMixin, DetailView):
    model = StudentLoan
    template_name = 'loans/student_loan_detail.html'
    context_object_name = 'loan'
    login_url = 'login'

class StudentLoanCreateView(LoginRequiredMixin, CreateView):
    model = StudentLoan
    form_class = StudentLoanForm
    template_name = 'loans/student_loan_form.html'
    login_url = 'login'
    success_url = reverse_lazy('student_loan_list')

    def form_valid(self, form):
        # Set the owner to the current user before saving the form
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_title'] = 'Student Loan Application'
        context['header_title'] = 'Apply for a New Student Loan'
        context['button_text'] = 'Submit Application'
        return context

class StudentLoanUpdateView(LoginRequiredMixin, UpdateView):
    model = StudentLoan
    form_class = StudentLoanForm
    template_name = 'loans/student_loan_form.html'
    login_url = 'login'
    success_url = reverse_lazy('student_loan_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_title'] = 'Update Student Loan Application'
        context['header_title'] = 'Update Your Student Loan'
        context['button_text'] = 'Modify Loan Details'
        return context

class StudentLoanDeleteView(LoginRequiredMixin, DeleteView):
    model = StudentLoan
    template_name = 'loans/student_loan_confirm_delete.html'
    login_url = 'login'
    success_url = reverse_lazy('student_loan_list')
