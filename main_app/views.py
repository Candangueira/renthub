from django.db import transaction
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.forms import UserCreationForm
# import forms.py
from django.contrib.auth import login, get_user_model
from .forms import CustomUserCreationForm, ReviewForm
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, Image
import os
import boto3
import uuid


User = get_user_model()


    # path('about', views.about, name='about'),
    # path('products', views.product_index, name='index'),
# Create your views here.

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html' )

def reviewform(request):
    review_form = ReviewForm
    return render(request, 'review_form.html', {
        'review_form': review_form
    })

# Profile Detail (LoginRequiredMixin)
class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'profile/profile_detail.html'
    context_object_name = 'profile'

    # # Prevent other users from accessing profiles that do not belong to them.
    def get_object(self, queryset=None):
        # Get the requested profile or raise a 404 error if not found
        profile = get_object_or_404(User, pk=self.kwargs['pk'])
        print('User: ', User)
        # Check if the authenticated user is owner  profile
        # profile.user != self.request.user
        print(self.request.user)
        if profile != self.request.user:
            print('profile: ', profile)
            print('self.request.user: ', self.request.user)
            # return PermissionDenied("permission Denied to views profile.")
            raise PermissionDenied("permission Denied to views profile.")
        print('Profile: ', profile)

        return profile
    
# Profile Edit (LoginRequiredMixin)
class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'profile/profile_form.html'
    fields = ['first_name', 'last_name', 'avatar', 'address', 'town', 'county', 'post_code', 'country']
    success_url = reverse_lazy('profile_detail')

    # Prevent other users from accessing profiles that do not belong to them.
    def get_object(self, queryset=None):
        user = super().get_object(queryset=queryset)
        print('user: ', user)
        if user != self.request.user:
            raise PermissionDenied("permission Denied to update profile.")
        return user
    
    # Redirect to detail page
    # https://docs.djangoproject.com/en/5.0/ref/urlresolvers/#reverse-lazy
    def get_success_url(self):
        return reverse_lazy('profile_detail', kwargs={'pk': self.object.pk})





# @transaction.atomic block unSucceeds create user to database
@transaction.atomic
def register(request):
    error_message = ''

    if request.method == 'POST':  
        form = CustomUserCreationForm(request.POST)  
        if form.is_valid():  
            form.save()
            # if user successful redirect to home page
            return redirect('login')
        else:
            # if not show error message or read error in terminal >> print(form.errors)
            print(form.errors)
            error_message = 'Invalid sign up - try again'
    else:
        form = CustomUserCreationForm()   

    context = {  
        'form':form,
        'error_message': error_message  
    }  
    return render(request, 'registration/signup.html', context)  


def add_image(request, product_id):
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        try:
            bucket = os.environ['S3_BUCKET']
            s3.upload_fileobj(photo_file, bucket, key)
            url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
            Image.objects.create(url=url, product_id=product_id)
        except Exception as e:
            print('An error occurred uploading file to S3')
            print(e)
    return redirect('product_detail', product_id=product_id)


# def register(request):
#     error_message = ''

#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)  # Log in the user after registration
#             return redirect('home')
#         else:
#             # print(form.errors)
#             error_message = 'Invalid sign up - try again'
#     else:
#         form = CustomUserCreationForm()

#     context = {
#         'form': form,
#         'error_message': error_message
#     }
#     return render(request, 'registration/signup.html', context)

### Products Views ###
# Function Based
# def product_list(request):
# 	products = Product.objects.all()
# 	return render(request, 'products/product_list.html', {
#         'products': products
# 	})

# Class Based
class ProductList(ListView):
    model = Product
    
class ProductDetail(DetailView):
    model = Product
    template_name = 'main_app/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['reviews'] = self.object.review_set.all()
        context['images'] = self.object.image_set.all()
        return context


class ProductCreate(CreateView):
    model = Product
    fields = ['product_name', 'description', 'price', 'category']
    success_url = '/products'

    def form_valid(self, form):
        # Assign the logged in user (self.request.user)
        form.instance.user = self.request.user  
        # Let the CreateView do its job as usual
        return super().form_valid(form)

    
class ProductUpdate(UpdateView):
    model = Product
    fields = ['product_name', 'description', 'price', 'category']
    
    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.id})

class ProductDelete(DeleteView):
    model = Product
    success_url = '/products'
