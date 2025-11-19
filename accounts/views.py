from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from laptop.models import Purchase
#from django.shortcuts import render
from .models import PointsTransaction

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # يسجل المستخدم بعد الإنشاء مباشرة
            return redirect('profile')  # يوجهه إلى الصفحة الرئيسية
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})



def profile(request):
    user = request.user
    purchases = Purchase.objects.filter(user=user)
    points = purchases.count() * 10  # كل عملية شراء = 10 نقاط مثلاً

    context = {
        'user': user,
        'points': points,
        'purchases': purchases,
    }
    return render(request, 'profile.html', context)

#b
def profile_view(request):
    user = request.user
    points_balance = PointsTransaction.get_user_balance(user)
    return render(request, 'profile.html', {'user': user, 'points_balance': points_balance})
#