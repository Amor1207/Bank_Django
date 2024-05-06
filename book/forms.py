from django import forms
from .models import Book,Publisher,Member,Profile,BorrowRecord
from .models import Transaction, SavingsAccount, CheckingAccount, Loan, HomeLoan, StudentLoan, Account
from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib import admin
from django.urls import reverse
from flatpickr import DatePickerInput, TimePickerInput, DateTimePickerInput
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class BookCreateEditForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('author',
                  'title',
                  'description',
                  'quantity', 
                  'category',
                  'publisher',
                  'floor_number',
                  "bookshelf_number")


class PubCreateEditForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ('name',
                  'city',
                  'contact',
                  )
        # fields="__all__"

class MemberCreateEditForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('name',
                  'gender',
                  'age',
                  'email',
                  'city', 
                  'phone_number',)


class ProfileForm(forms.ModelForm):

    
    class Meta:
        model = Profile
        fields = ( 'profile_pic',
                  'bio', 
                  'phone_number',
                  'email')


class BorrowRecordCreateForm(forms.ModelForm):

    borrower = forms.CharField(label='Borrrower', 
                    widget=forms.TextInput(attrs={'placeholder': 'Search Member...'}))
    
    book = forms.CharField(help_text='type book name')

    class Meta:
        model = BorrowRecord
        fields=['borrower','book','quantity','start_day','end_day']

        widgets = {
            'start_day': DatePickerInput(options = {  "dateFormat": "Y-m-d", }),
            'end_day': DatePickerInput(options = {  "dateFormat": "Y-m-d", }),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['user','account', 'transaction_type', 'amount', 'status', 'transaction_date', 'completion_date', 'description', 'payment_method']
        widgets = {
            'transaction_date': DatePickerInput(options={"dateFormat": "Y-m-d"}),
            'completion_date': DatePickerInput(options={"dateFormat": "Y-m-d"}),
            'amount': forms.NumberInput(attrs={'step': '0.01'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TransactionForm, self).__init__(*args, **kwargs)
        # Ensure the account field shows all related savings accounts
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['account'].queryset = Account.objects.filter(owner=user)
        self.fields['account'].label = "Account"
        self.fields['status'].widget = forms.Select(choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ])
        self.fields['payment_method'].widget = forms.Select(choices=[
            ('cash', 'Cash'),
            ('credit_card', 'Credit Card'),
            ('paypal', 'PayPal')
        ])

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("The amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        status = cleaned_data.get('status')

        if transaction_type == 'refund' and status != 'pending':
            raise forms.ValidationError("Refunds must initially be marked as pending.")
        return cleaned_data

class SavingsAccountForm(forms.ModelForm):
    class Meta:
        model = SavingsAccount
        fields = ['owner', 'balance', 'interest_rate']
        widgets = {
            # 'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'owner': forms.Select(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_balance(self):
        balance = self.cleaned_data.get('balance')
        if balance and balance < 0:
            raise ValidationError("The balance cannot be negative.")
        return balance

    def clean_interest_rate(self):
        interest_rate = self.cleaned_data.get('interest_rate')
        if interest_rate and (interest_rate < 0 or interest_rate > 100):
            raise ValidationError("Interest rate must be between 0 and 100 percent.")
        return interest_rate

    def save(self, commit=True):
        account = super().save(commit=False)
        # You can add any custom save logic here
        if commit:
            account.save()
        return account

class CheckingAccountForm(forms.ModelForm):
    class Meta:
        model = CheckingAccount
        fields = ['owner', 'balance', 'overdraft_limit', 'transaction_fee', 'daily_withdrawal_limit']
        widgets = {
            'owner': forms.Select(attrs={'class': 'form-control'}),
            # 'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'overdraft_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transaction_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'daily_withdrawal_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_balance(self):
        balance = self.cleaned_data.get('balance')
        if balance and balance < 0:
            raise forms.ValidationError("The balance must be zero or positive unless an overdraft is approved.")
        return balance

    def clean_overdraft_limit(self):
        overdraft_limit = self.cleaned_data.get('overdraft_limit')
        if overdraft_limit < 0:
            raise forms.ValidationError("Overdraft limit cannot be negative.")
        return overdraft_limit

    def clean_transaction_fee(self):
        transaction_fee = self.cleaned_data.get('transaction_fee')
        if transaction_fee < 0:
            raise forms.ValidationError("Transaction fee cannot be negative.")
        return transaction_fee

    def clean_daily_withdrawal_limit(self):
        daily_withdrawal_limit = self.cleaned_data.get('daily_withdrawal_limit')
        if daily_withdrawal_limit <= 0:
            raise forms.ValidationError("Daily withdrawal limit must be greater than zero.")
        return daily_withdrawal_limit

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['loan_amount', 'loan_term', 'start_date', 'due_date', 'interest_rate']
        widgets = {
            'start_date': DatePickerInput(options={"dateFormat": "Y-m-d"}),
            'due_date': DatePickerInput(options={"dateFormat": "Y-m-d"}),
        }

class HomeLoanForm(LoanForm):
    class Meta(LoanForm.Meta):
        model = HomeLoan
        fields = LoanForm.Meta.fields + ['property_address', 'property_value']

class StudentLoanForm(LoanForm):
    class Meta(LoanForm.Meta):
        model = StudentLoan
        fields = LoanForm.Meta.fields + ['school_name', 'course']