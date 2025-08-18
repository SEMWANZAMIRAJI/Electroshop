from django.shortcuts import render, redirect
from urllib.parse import quote_plus
# Create your views here.
from django.views.generic import ListView, TemplateView, View
from django.shortcuts import render, redirect
from .models import Product, Order
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
import os
import pandas as pd
from django.conf import settings

class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    reverse_lazy = 'product_list'
    paginate_by = 6


class Homepage(ListView):
    model = Product
    template_name = 'store/home.html'
    context_object_name = 'products'
    
class AddToCartView(View):
    def post(self, request, pk):
        cart = request.session.get('cart', {})

        # Ensure cart is a dictionary
        if not isinstance(cart, dict):
            cart = {}

        pk = str(pk)  # keys must be strings for session
        if pk in cart:
            cart[pk] += 1
        else:
            cart[pk] = 1
        request.session['cart'] = cart
        return redirect('cart')


class CartView(TemplateView):
    template_name = 'store/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get('cart', {})
        cart_items = []
        total = 0
        whatsapp_message_lines = ["Hello, I want to order these products:"]

        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(pk=product_id)
                subtotal = product.price * quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
                whatsapp_message_lines.append(f"- {product.name} x {quantity}")
            except Product.DoesNotExist:
                continue

        whatsapp_message_lines.append(f"Total Price: TZS{total:.2f}")
        whatsapp_message_lines.append("Please confirm availability and shipping details. Thank you!")

        message_text = quote_plus("\n".join(whatsapp_message_lines))
        whatsapp_number = "255624313810"
        whatsapp_url = f"https://wa.me/{whatsapp_number}?text={message_text}"

        context['cart_items'] = cart_items
        context['total'] = total
        context['whatsapp_order_link'] = whatsapp_url
        return context


class CheckoutView(View):
    def get(self, request):
        cart = request.session.get('cart', [])
        products = Product.objects.filter(id__in=cart)
        return render(request, 'store/checkout.html', {'products': products})

    def post(self, request):
        name = request.POST['name']
        phone = request.POST['phone']
        cart = request.session.get('cart', [])
        products = Product.objects.filter(id__in=cart)

        order = Order.objects.create(customer_name=name, phone_number=phone)
        order.products.set(products)
        order.save()
        request.session['cart'] = []
        return redirect('success')

class OrderSuccessView(TemplateView):
    template_name = 'store/success.html'


class CustomLoginView(LoginView):
    template_name = 'store/login.html'

    def get_success_url(self):
        if self.request.user.username == 'nuhu':
            return reverse_lazy('product_create')
        return reverse_lazy('product_list')


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    fields = ['name', 'description', 'price', 'image']
    template_name = 'store/create_product.html'
    success_url = reverse_lazy('product_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username != 'nuhu':
            return HttpResponseForbidden("Only seller 'nuhu' can create products.")
        return super().dispatch(request, *args, **kwargs)
