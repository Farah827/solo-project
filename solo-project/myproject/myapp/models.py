from django.db import models
import re
from datetime import date , datetime
import bcrypt
from django.db.models import Sum   
from decimal import Decimal  

class UserManager(models.Manager):
    def registration_validator(self,postData):
        errors ={}

        if len(postData['user_name']) < 2 or not postData['user_name'].isalpha():
            errors['user_name'] = "user_name name must be at least 2 character"


        EMAIL_REGEX =  re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        if not EMAIL_REGEX.match(postData['email']):
            errors['email'] = "Invalid email address"
        if User.objects.filter(email = postData['email']):
            errors['email_unique'] = "This Email already regustered"

        if len(postData['password']) < 8 :
            errors['password'] = "Password must be at least 8 character"    
        if postData['password'] != postData['confirm_password']:
            errors['confirm_pw'] = "Passwords dont match"  

        
        return errors            

    


    def login_validator(self, postData):
        errors = {}
        user = User.objects.filter(email=postData.get('email')).first()
        if not user:
            errors['login'] = "Invalid Email or Password"  # email not found
        elif not bcrypt.checkpw(postData.get('password', '').encode(), user.password.encode()):
            errors['login'] = "Invalid Email or Password"  # password wrong
        return errors






class User(models.Model):
    user_name = models.CharField(max_length=45)
    email = models.EmailField(unique=True, max_length=45)
    password = models.CharField(max_length=128)  # Django usually hashes, so longer is better
    role = models.CharField(
        max_length=10,
        choices=[('kid', 'Kid'), ('parent', 'Parent')],
        default='kid'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Self-relation: parent has many kids
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children'
    )
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)  # weekly allowance
    remaining_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)

    objects = UserManager()



    def get_balance(self):
        deposits = self.transactions.filter(type='Deposit').aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        withdrawals = self.transactions.filter(type='Withdrawal').aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        goal_contributions = self.transactions.filter(type='Goal Contribution').aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

        balance = deposits - withdrawals - goal_contributions
        return balance





class SavingsGoal(models.Model):
    kid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='savings_goals',
        limit_choices_to={'role': 'kid'}
    )
    name = models.CharField(max_length=45)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    saved_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)





class Transaction(models.Model):
    kid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        limit_choices_to={'role': 'kid'}
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(
        max_length=20,
        choices=[('Deposit', 'Deposit'), ('Withdrawal', 'Withdrawal'), ('Goal Contribution', 'Goal Contribution')]
    )
    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)    