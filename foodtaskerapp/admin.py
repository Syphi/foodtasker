from django.contrib import admin

# Register your models here.
from foodtaskerapp.models import Restaurant
from foodtaskerapp.models import Customer
from foodtaskerapp.models import Driver
from foodtaskerapp.models import Meal
from foodtaskerapp.models import Order
from foodtaskerapp.models import OrderDetails

admin.site.register(Restaurant)
admin.site.register(Customer)
admin.site.register(Driver)
admin.site.register(Meal)
admin.site.register(Order)
admin.site.register(OrderDetails)
