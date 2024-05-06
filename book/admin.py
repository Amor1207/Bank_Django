from django.contrib import admin

# Register your models here.
from.models import Category,Publisher,Profile,Member,BorrowRecord, UserProfile,SavingsAccount

from .forms import BorrowRecordCreateForm

# @admin.register(Member)
# class MemberAdmin(AjaxSelectAdmin):
#     form = BorrowRecordCreateForm

admin.site.register(Member)
admin.site.register(BorrowRecord)

# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'get_balance']
#
#     def get_balance(self, obj):
#         # 假设一个用户可能有多个储蓄账户，我们这里取所有账户余额的总和
#         return sum([account.balance for account in SavingsAccount.objects.filter(owner=obj.user)])
#     get_balance.short_description = "Balance"