from django.shortcuts import render ,redirect
from django.contrib import messages
from .models import *
import bcrypt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET






def home(request):
    return render(request, 'myapp/home.html')

def login_page(request):
    return render(request, "myapp/login.html")

def register_page(request):
    """Render the signup page"""
    return render(request, 'myapp/signup.html')

def register(request):
    if request.method == 'POST':
        errors = User.objects.registration_validator(request.POST)

        if errors:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect('register_page')  

        # Hash password
        pw_hash = bcrypt.hashpw(request.POST['password'].encode(), bcrypt.gensalt()).decode()

        # Create parent user only
        user = User.objects.create(
            user_name=request.POST['user_name'],
            email=request.POST['email'],
            role='parent',  # force role as parent
            password=pw_hash
        )

        # Store session
        request.session['user_id'] = user.id
        request.session['role'] = user.role   # ✅ store role
        request.session['user_name'] = user.user_name

        return redirect('parent_dashboard')   # ✅ go directly to dashboard
    return redirect('register_page')

def login(request):
    if request.method == 'POST':
        errors = User.objects.login_validator(request.POST)  # use the validator

        if errors:
            for key, value in errors.items():
                messages.error(request, value)  # add error messages
            return redirect('login_page')  # redirect back

        # Get the user after validation
        user = User.objects.get(email=request.POST['email'])

        # Store session data
        request.session['user_id'] = user.id
        request.session['role'] = user.role
        request.session['user_name'] = user.user_name

        # Redirect based on role
        if user.role == 'parent':
            return redirect('parent_dashboard')
        elif user.role == 'kid':
            return redirect('kid_dashboard')

    return redirect('login_page')




def parent_dashboard(request):
    if 'user_id' not in request.session or request.session['role'] != 'parent':
        return redirect('/')  # only parents allowed

    parent = User.objects.get(id=request.session['user_id'])
    kids = parent.children.all()  # all kids related to this parent

    context = {
        "user_name": parent.user_name,
        "kids": kids
    }
    return render(request, 'myapp/parent_dashboard.html', context)


def parent_tips(request):
    if 'user_id' not in request.session or request.session['role'] != 'parent':
        return redirect('login')

    parent = get_object_or_404(User, id=request.session['user_id'], role='parent')

    return render(request, "myapp/parent_tips.html", {
        "user_name": parent.user_name
    })


def logout(request):
    request.session.flush()
    return redirect('/')






def add_kid(request):
    if request.method == 'POST' and request.session.get('role') == 'parent':
        if request.POST.get('form_type') == 'add_kid':  
            postData = request.POST

            # Run your validator
            errors = User.objects.registration_validator(postData)

            if errors:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":  
                    # AJAX → return JSON
                    return JsonResponse({"status": "error", "errors": errors})
                else:
                    # Normal POST → use messages + redirect
                    for key, value in errors.items():
                        messages.error(request, value)
                    return redirect('parent_dashboard')

            # ✅ If no errors → create kid
            pw_hash = bcrypt.hashpw(postData['password'].encode(), bcrypt.gensalt()).decode()
            parent = User.objects.get(id=request.session['user_id'])

            kid = User.objects.create(
                user_name=postData['user_name'],
                email=postData['email'],
                role='kid',
                password=pw_hash,
                parent=parent
            )

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "status": "success",
                    "message": f"Kid account '{kid.user_name}' added successfully!",
                    "kid": {
                        "id": kid.id,
                        "user_name": kid.user_name,
                        "email": kid.email,
                        "allowance": kid.remaining_allowance,
                        "balance": kid.get_balance(),
                    }
                })
            else:
                messages.success(request, f"Kid account '{postData['user_name']}' added successfully!")

    return redirect('parent_dashboard')



def kid_dashboard(request):
    if 'user_id' not in request.session or request.session['role'] != 'kid':
        return redirect('/')

    kid = User.objects.get(id=request.session['user_id'])

    context = {
        "user_name": kid.user_name,
        "balance": kid.get_balance(),
        "goals_count": kid.savings_goals.count(),
        "transactions_count": kid.transactions.count(),
        "remaining_allowance": kid.remaining_allowance,
        "kid":kid,
    }
    return render(request, "myapp/kid_dashboard.html", context)




def kid_balance(request):
    kid = User.objects.get(id=request.session['user_id'])
    return render(request, "myapp/kid_balance.html", {
        "balance": kid.get_balance()
    })


def kid_goals(request):
    # Ensure only logged-in kids can access
    if 'user_id' not in request.session or request.session['role'] != 'kid':
        return redirect('login')  

    kid = User.objects.get(id=request.session['user_id'])
    goals = kid.savings_goals.all()

    # add progress percentage
    for g in goals:
        if g.target_amount > 0:
            g.progress = int((g.saved_amount / g.target_amount) * 100)
        else:
            g.progress = 0

    return render(request, "myapp/kid_goals.html", {"goals": goals , "kid":kid})




def kid_transactions(request):
    kid = User.objects.get(id=request.session['user_id'])
    transactions = kid.transactions.order_by('-created_at')
    return render(request, "myapp/kid_transactions.html", {"transactions": transactions , "kid":kid})

def kid_rewards(request):
    if 'user_id' not in request.session or request.session['role'] != 'kid':
        return redirect('login')

    kid = User.objects.get(id=request.session['user_id'])
    stars = 0

    for goal in kid.savings_goals.all():
        if goal.saved_amount >= goal.target_amount:
            stars += 3
        elif goal.saved_amount >= goal.target_amount / 2:
            stars += 1

    # pass a list to template for iteration
    return render(request, "myapp/kid_rewards.html", {
        "stars": stars,
        "earned_list": list(range(stars))  ,
        "kid":kid
    })




def add_goal(request):
    if request.method == "POST" and 'user_id' in request.session and request.session['role'] == 'kid':
        kid = User.objects.get(id=request.session['user_id'])
        name = request.POST.get('name')
        target = request.POST.get('target_amount')

        if not name or not target:
            messages.error(request, "Please provide goal name and target amount")
            return redirect('kid_goals')

        SavingsGoal.objects.create(
            kid=kid,
            name=name,
            target_amount=Decimal(target)
        )
        messages.success(request, "Goal created successfully!")

    return redirect('kid_goals')

def make_transaction(request):
    if request.method == "POST":
        kid = User.objects.get(id=request.session['user_id'])
        if kid.role != "kid":
            return JsonResponse({"success": False, "error": "Unauthorized user!"})

        try:
            amount = Decimal(request.POST.get("amount", "0"))
            t_type = request.POST.get("type")
            goal_id = request.POST.get("goal_id")  # optional

            if amount <= 0:
                return JsonResponse({"success": False, "error": "Amount must be greater than 0!"})

            # Handle Deposit
            if t_type == "Deposit":
                if amount > kid.remaining_allowance:
                    return JsonResponse({
                        "success": False,
                        "error": f"Cannot deposit more than remaining allowance (${kid.remaining_allowance})!"
                    })
                kid.remaining_allowance -= amount
                kid.save()
                Transaction.objects.create(
                    kid=kid,
                    amount=amount,
                    type=t_type
                )
                message = f"Deposited ${amount:.2f} successfully!"
                return JsonResponse({
                    "success": True,
                    "new_balance": str(kid.get_balance()),
                    "remaining_allowance": str(kid.remaining_allowance),
                    "message": message
                })

            # Handle Withdrawal
            elif t_type == "Withdrawal":
                balance = kid.get_balance()
                if amount > balance:
                    return JsonResponse({"success": False, "error": "Not enough balance to withdraw!"})
                Transaction.objects.create(
                    kid=kid,
                    amount=amount,
                    type=t_type
                )
                message = f"Withdrew ${amount:.2f} successfully!"
                return JsonResponse({
                    "success": True,
                    "new_balance": str(kid.get_balance()),
                    "message": message
                })

            # Handle Goal Contribution (from current savings)
            elif t_type == "Goal Contribution":
                if not goal_id:
                    return JsonResponse({"success": False, "error": "Goal not specified!"})
                
                goal = SavingsGoal.objects.get(id=goal_id, kid=kid)
                balance = kid.get_balance()
                if amount > balance:
                    return JsonResponse({
                        "success": False,
                        "error": f"Cannot contribute more than current savings (${balance})!"
                    })

                # Add to goal
                goal.saved_amount += amount
                goal.save()

                # Record transaction as Goal Contribution
                Transaction.objects.create(
                    kid=kid,
                    amount=amount,
                    type=t_type,
                    goal=goal
                )

                return JsonResponse({
                    "success": True,
                    "new_balance": str(kid.get_balance()),  # balance decreases
                    "goal_saved": str(goal.saved_amount),
                    "goal_progress": int((goal.saved_amount / goal.target_amount) * 100),
                    "message": f"Added ${amount:.2f} to goal '{goal.name}'!"
                })

            else:
                return JsonResponse({"success": False, "error": "Invalid transaction type!"})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})




def parent_kid_goals(request, kid_id):
    if 'user_id' not in request.session or request.session['role'] != 'parent':
        return redirect('/')

    parent = User.objects.get(id=request.session['user_id'])
    kid = User.objects.filter(id=kid_id, parent=parent).first()

    if not kid:
        messages.error(request, "You are not authorized to view this kid’s goals.")
        return redirect('parent_dashboard')

    goals = kid.savings_goals.all()
    for g in goals:
        if g.target_amount > 0:
            g.progress = int((g.saved_amount / g.target_amount) * 100)
        else:
            g.progress = 0

    return render(request, "myapp/parent_kid_goals.html", {
        "kid": kid,
        "goals": goals
    })


def parent_kid_transactions(request, kid_id):
    if 'user_id' not in request.session or request.session['role'] != 'parent':
        return redirect('/')

    parent = User.objects.get(id=request.session['user_id'])
    kid = User.objects.filter(id=kid_id, parent=parent).first()

    if not kid:
        messages.error(request, "You are not authorized to view this kid’s transactions.")
        return redirect('parent_dashboard')

    transactions = kid.transactions.order_by('-created_at')

    return render(request, "myapp/parent_kid_transactions.html", {
        "kid": kid,
        "transactions": transactions
    })


def parent_kid_rewards(request, kid_id):
    if 'user_id' not in request.session or request.session['role'] != 'parent':
        return redirect('/')

    parent = User.objects.get(id=request.session['user_id'])
    kid = User.objects.filter(id=kid_id, parent=parent).first()

    if not kid:
        messages.error(request, "You are not authorized to view this kid’s rewards.")
        return redirect('parent_dashboard')

    stars = 0
    for goal in kid.savings_goals.all():
        if goal.saved_amount >= goal.target_amount:
            stars += 3
        elif goal.saved_amount >= goal.target_amount / 2:
            stars += 1

    return render(request, "myapp/parent_kid_rewards.html", {
        "kid": kid,
        "stars": stars,
        "star_range": range(stars)
    })




def remove_kid(request, kid_id):
    if 'user_id' not in request.session or request.session['role'] != 'parent':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    parent = User.objects.get(id=request.session['user_id'])
    kid = get_object_or_404(User, id=kid_id, parent=parent, role='kid')

    if request.method == "POST":
        kid_name = kid.user_name
        kid.delete()

        # ✅ Detect AJAX request
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                'status': 'success',
                'message': f"{kid_name} was removed successfully!",
                'id': kid_id
            })

        # fallback for non-AJAX
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.success(request, f"{kid_name} was removed successfully!")
        return redirect('parent_dashboard')

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



def set_allowance(request, kid_id):
    if request.method == "POST":
        kid = get_object_or_404(User, id=kid_id, role='kid')
        try:
            new_allowance = float(request.POST.get('allowance', 0))
            if new_allowance <= 0:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"status": "error", "message": "❌ Allowance must be greater than 0!"})
                messages.error(request, "❌ Allowance must be greater than 0!")
            else:
                kid.allowance = new_allowance
                kid.remaining_allowance = new_allowance
                kid.save()
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({
                        "status": "success",
                        "message": f"✅ {kid.user_name}'s allowance is now ${new_allowance}!",
                        "new_allowance": new_allowance
                    })
                messages.success(request, f"✅ {kid.user_name}'s allowance is now ${new_allowance}!")
        except ValueError:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"status": "error", "message": "❌ Please enter a valid number"})
            messages.error(request, "❌ Please enter a valid number")

    return redirect('parent_dashboard')




from django.template.loader import render_to_string




