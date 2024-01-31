from django.shortcuts import render
from django.views.generic import View
from .models import User
from .forms import ReviewForm
# Create your views here.

def home(request):
    return render(request, 'home.html')

def reviewform(request):
    review_form = ReviewForm
    return render(request, 'review_form.html', {
        'review_form': review_form
    })

class Profile(View):
    model = User
    path = 'renthub/profile.html'
    def get(self, request, pk):
        user = User.objects.get(pk=pk)
        return render(request,'renthub/profile.html', {

            'user': user,

            }
        )