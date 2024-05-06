from django.db import models
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
# from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import uuid
from PIL import Image
from django.core.exceptions import ValidationError
from django.utils.timezone import now
import math
import random

BOOK_STATUS =(
    (0, "On loan"),
    (1, "In Stock"),
)

FLOOR =(
    (1, "1st"),
    (2, "2nd"),
    (3, "3rd"),
)

OPERATION_TYPE =(
    ("success", "Create"),
    ("warning","Update"),
    ("danger","Delete"),
    ("info",'Close')
)

GENDER=(
    ("m","Male"),
    ("f","Female"),
)

BORROW_RECORD_STATUS=(
    (0,'Open'),
    (1,'Closed')
)

class Category(models.Model):
    
    name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    def get_absolute_url(self): 
        return reverse('category_list')

    # class Meta:
    #     db_table='category'

class Publisher(models.Model):
    
    name = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    contact = models.EmailField(max_length=50,blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_by=models.CharField(max_length=20,default='yaozeliang')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self): 
        return reverse('publisher_list')

class Book(models.Model):
    author = models.CharField("Author",max_length=20)
    title = models.CharField('Title',max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField('Created Time',default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    total_borrow_times = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=10)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='category'
    )

    publisher=models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='publisher'
    )

    status=models.IntegerField(choices=BOOK_STATUS,default=1)
    floor_number=models.IntegerField(choices=FLOOR,default=1)
    bookshelf_number=models.CharField('Bookshelf Number',max_length=10,default='0001')
    updated_by=models.CharField(max_length=20,default='yaozeliang')

    def get_absolute_url(self): 
        return reverse('book_list')
    
    def __str__(self):
        return self.title

class UserActivity(models.Model):
    created_by=models.CharField(default="",max_length=20)
    created_at =models.DateTimeField(auto_now_add=True)
    operation_type=models.CharField(choices=OPERATION_TYPE,default="success",max_length=20)
    target_model = models.CharField(default="",max_length=20)
    detail = models.CharField(default="",max_length=50)

    def get_absolute_url(self): 
        return reverse('user_activity_list')

class Member(models.Model):
    name = models.CharField(max_length=50, blank=False)
    age = models.PositiveIntegerField(default=20)
    gender = models.CharField(max_length=10,choices=GENDER,default='m')

    city = models.CharField(max_length=20, blank=False)
    email = models.EmailField(max_length=50,blank=True)
    phone_number = models.CharField(max_length=30,blank=False)

    created_at= models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=20,default="")
    updated_by = models.CharField(max_length=20,default="")
    updated_at = models.DateTimeField(auto_now=True)

    card_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    card_number = models.CharField(max_length=8,default="")
    expired_at = models.DateTimeField(default=timezone.now)

    def get_absolute_url(self): 
        return reverse('member_list')
    
    def save(self, *args, **kwargs):
        self.card_number = str(self.card_id)[:8]
        self.expired_at = timezone.now()+relativedelta(years=1)
        return super(Member, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


# UserProfile
class Profile(models.Model):
    user = models.OneToOneField(User,null=True,on_delete=models.CASCADE)
    bio = models.TextField()
    profile_pic = models.ImageField(upload_to="profile/%Y%m%d/", blank=True,null=True)
    phone_number = models.CharField(max_length=30,blank=True)
    email = models.EmailField(max_length=50,blank=True)

    def save(self, *args, **kwargs):
        # 调用原有的 save() 的功能
        profile = super(Profile, self).save(*args, **kwargs)

        # 固定宽度缩放图片大小
        if self.profile_pic and not kwargs.get('update_fields'):
            image = Image.open(self.profile_pic)
            (x, y) = image.size
            new_x = 400
            new_y = int(new_x * (y / x))
            resized_image = image.resize((new_x, new_y), Image.ANTIALIAS)
            resized_image.save(self.profile_pic.path)

        return profile

    def __str__(self):
        return str(self.user)

    def get_absolute_url(self): 
        return reverse('home')


# Borrow Record

class BorrowRecord(models.Model):

    borrower = models.CharField(blank=False,max_length=20)
    borrower_card = models.CharField(max_length=8,blank=True)
    borrower_email = models.EmailField(max_length=50,blank=True)
    borrower_phone_number  = models.CharField(max_length=30,blank=True)
    book = models.CharField(blank=False,max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    start_day = models.DateTimeField(default=timezone.now)
    end_day = models.DateTimeField(default=timezone.now()+timedelta(days=7))
    periode = models.PositiveIntegerField(default=0)

    open_or_close = models.IntegerField(choices=BORROW_RECORD_STATUS,default=0)
    delay_days = models.IntegerField(default=0)
    final_status = models.CharField(max_length=10,default="Unknown")

    created_at= models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=20,blank=True)
    closed_by = models.CharField(max_length=20,default="")
    closed_at = models.DateTimeField(auto_now=True)

    @property
    def return_status(self):
        if self.final_status!="Unknown":
            return self.final_status
        elif self.end_day.replace(tzinfo=None) > datetime.now()-timedelta(hours=24):
            return 'On time'
        else:
            return 'Delayed'

    @property
    def get_delay_number_days(self):
        
        if self.delay_days!=0:
            return self.delay_days
        elif self.return_status=='Delayed':
            return (datetime.now()-self.end_day.replace(tzinfo=None)).days
        else:
            return 0


    def get_absolute_url(self): 
        return reverse('record_list')

    def __str__(self):
        return self.borrower+"->"+self.book
    
    def save(self, *args, **kwargs):
        # profile = super(Profile, self).save(*args, **kwargs)
        self.periode =(self.end_day - self.start_day).days+1
        return super(BorrowRecord, self).save(*args, **kwargs)


class Account(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    account_type = models.CharField(max_length=10, choices=[('savings', 'Savings'), ('checking', 'Checking')])
    interest_rate = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = False

    def __str__(self):
        return f"{self.owner.username} - {self.account_number} - {self.account_type}"

    def update_balance(self, amount, transaction_type):
        if transaction_type == 'deposit':
            self.balance += amount
        elif transaction_type == 'withdrawal':
            if amount > self.balance:
                raise ValueError("Insufficient funds")
            self.balance -= amount

    def save(self, *args, **kwargs):
        if not self.account_number:
            # 生成账户号码直到找到一个唯一的账户号码
            while True:
                new_account_number = 'AC' + str(random.randint(1000000, 9999999))
                if not Account.objects.filter(account_number=new_account_number).exists():
                    self.account_number = new_account_number
                    break
        super().save(*args, **kwargs)

class SavingsAccount(Account):
    # 添加特定于储蓄账户的字段
    minimum_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Minimum balance required in the account')
    is_joint_account = models.BooleanField(default=False, help_text='Indicates if the account is a joint account')
    annual_fees = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text='Annual fees applicable to the savings account')

    def apply_interest(self):
        """Apply interest to the balance based on the interest rate and current balance."""
        if self.balance > self.minimum_balance:
            interest = self.balance * (self.interest_rate / 100)
            self.balance += interest
            self.save()

    def check_minimum_balance(self):
        """Check if the account balance is above the minimum required balance."""
        if self.balance < self.minimum_balance:
            raise ValueError("Account balance is below the minimum required balance.")

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = 'SA'+str(uuid.uuid4())[:8]  # Generate a random UUID and take first 8 characters
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{super().__str__()} - Joint Account: {'Yes' if self.is_joint_account else 'No'}"

class CheckingAccount(Account):
    overdraft_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Maximum overdraft limit allowed for the account')
    transaction_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text='Fee charged per transaction')
    daily_withdrawal_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Maximum amount that can be withdrawn in a day')

    def apply_fees(self):
        """Apply transaction fees to the account if applicable."""
        if self.balance < 0:  # Assuming balance can go negative up to the overdraft limit
            self.balance -= self.transaction_fee
            self.save()

    def check_withdrawal_limit(self, amount):
        """Check if the withdrawal amount is within the daily limit."""
        if amount > self.daily_withdrawal_limit:
            raise ValueError("Withdrawal amount exceeds daily limit.")

    def __str__(self):
        return f"{super().__str__()} - Overdraft Limit: {self.overdraft_limit}"

    def update_balance(self, amount, transaction_type):
        """Override the update_balance method to include checking for overdraft and applying fees."""
        super().update_balance(amount, transaction_type)
        if transaction_type == 'withdrawal':
            self.apply_fees()
            self.check_withdrawal_limit(amount)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = 'CH'+str(uuid.uuid4())[:8]  # Generate a random UUID and take first 8 characters
        super().save(*args, **kwargs)

class Transaction(models.Model):
    transaction_type_choices = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions',null=True)
    transaction_type = models.CharField(max_length=50, choices=transaction_type_choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    status = models.CharField(max_length=50)
    transaction_date = models.DateTimeField(default=now)
    completion_date = models.DateTimeField(null=True, blank=True)
    description = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.pk and self.transaction_type in ['deposit', 'withdrawal']:
            self.account.update_balance(self.amount, self.transaction_type)
        super().save(*args, **kwargs)

    def is_complete(self):
        return self.status == 'Completed'

    def mark_as_completed(self):
        self.status = 'Completed'
        self.completion_date = now()
        self.save()

class Loan(Account):
    LOAN_STATUS_CHOICES = [
        ('active', 'Active'),
        ('overdue', 'Overdue'),
        ('paid_off', 'Paid Off'),
    ]
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount of the loan")
    loan_term = models.IntegerField(help_text="Term of the loan in months")
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monthly repayment amount", blank=True, null=True)
    start_date = models.DateField(default=timezone.now, help_text="The date when the loan was issued")
    due_date = models.DateField(help_text="The date by which the loan should be fully repaid")
    status = models.CharField(max_length=10, choices=LOAN_STATUS_CHOICES, default='active', help_text="Current status of the loan")

    def calculate_monthly_payment(self):
        # Monthly interest rate (annual rate / 12 months)
        monthly_interest_rate = self.interest_rate / 100 / 12 if self.interest_rate else 0
        # Total number of payments
        total_payments = self.loan_term

        if monthly_interest_rate > 0:
            # Calculate monthly payment based on compound interest formula
            monthly_payment = (
                self.loan_amount * monthly_interest_rate * math.pow(1 + monthly_interest_rate, total_payments)
            ) / (math.pow(1 + monthly_interest_rate, total_payments) - 1)
        else:
            # If interest rate is 0%, simplify the calculation
            monthly_payment = self.loan_amount / total_payments

        self.monthly_payment = monthly_payment
        self.save()

    def __str__(self):
        return f"{super().__str__()} - {self.loan_amount} at {self.interest_rate}% for {self.loan_term} months"

    def check_due_status(self):
        """ Update the status of the loan based on the due date and current date. """
        if self.due_date < timezone.now().date():
            self.status = 'overdue'
        self.save()

    def days_until_next_repayment_percent(self):
        """ Calculate the number of days until the next repayment date. """
        if self.due_date and self.status != 'paid_off':
            today = timezone.now().date()
            return int(100 * (self.due_date - today).days/(self.due_date - self.start_date).days) if self.due_date > today else 100
        return 100

    def days_until_next_repayment(self):
        """ Calculate the number of days until the next repayment date. """
        if self.due_date and self.status != 'paid_off':
            today = timezone.now().date()
            return (self.due_date - today).days if self.due_date > today else 0
        return 0

    class Meta:
        ordering = ['-start_date']  # Orders loans starting from the most recent
        verbose_name = 'Loan'
        verbose_name_plural = 'Loans'

class HomeLoan(Loan):
    property_address = models.CharField(max_length=255, help_text="Address of the property")
    property_value = models.DecimalField(max_digits=12, decimal_places=2, help_text="Appraised value of the property")

    def __str__(self):
        return f"{super().__str__()} - Property at {self.property_address}"

class StudentLoan(Loan):
    school_name = models.CharField(max_length=255, help_text="Name of the institution")
    course = models.CharField(max_length=255, help_text="Course of study")

    def __str__(self):
        return f"{super().__str__()} - Studying {self.course} at {self.school_name}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Possibly other user-specific settings or data

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create the user profile
        profile = UserProfile.objects.create(user=instance)

        # Create default savings and checking accounts
        SavingsAccount.objects.create(owner=instance, account_number="S" + str(instance.pk).zfill(6))
        # CheckingAccount.objects.create(owner=instance, account_number="C" + str(instance.pk).zfill(6))
    else:
        # Update the user profile
        instance.userprofile.save()






