from django.http import JsonResponse

import json
from oauth2_provider.models import AccessToken
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from foodtaskerapp.models import Restaurant
from foodtaskerapp.models import Meal
from foodtaskerapp.models import Order
from foodtaskerapp.models import OrderDetails
from foodtaskerapp.models import Driver
from foodtaskerapp.serializer import RestaurantSerializer
from foodtaskerapp.serializer import MealSerializer
from foodtaskerapp.serializer import OrderSerializer
from datetime import timedelta

##########
#CUSTOMERS
##########

def customer_get_restaurant(request):
    restaurant = RestaurantSerializer(
        Restaurant.objects.all().order_by("-id"),
        many=True,
        context = {'request': request},
    ).data

    return JsonResponse({'restauant': restaurant})


def customer_get_meals(request, restaurant_id):
    meals = MealSerializer(
        Meal.objects.filter(restaurant_id=restaurant_id).order_by("-id"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"meals": meals})

@csrf_exempt
def customer_add_order(request):
    """
        :param
            access_token
            restaurant_id
            address
            order_details(json format) example:
                [{"meal_id": 1, "quantity":2},{"meal_id": 2, "quantity":3}]
            stripe_token

    :return:
        {"status":"sucsess"}
    """
    if request.method == "POST":
        # Get token
        #access_token = AccessToken.objects.get(token=request.data.get('access_token'), expires__gt=timezone.now())
        # try:
        tok = request.POST.get("access_token")
        print(tok)
        allobj = AccessToken.objects.all()
        print(allobj)
        access_token = AccessToken.objects.get(token=tok, expires__gt=timezone.now())
        # except AccessToken.DoesNotExist:
        #     access_token = AccessToken.objects.create(
        #
        #     )

        # Get profile
        customer = access_token.user.customer

        if Order.objects.filter(customer=customer).exclude(status=Order.DELIVERED):
            return JsonResponse({'status': 'fail', 'error': "Your last order must be complited."})

        # Check Adress
        if not request.POST["address"]:
            return JsonResponse({'status': 'fail', 'error': "Address is required."})

        # Get Order details
        order_details = json.loads(request.POST['order_details'])

        order_total = 0
        for meal in order_details:
            order_total += Meal.objects.get(id=meal["meal_id"]).price * meal["quantity"]

        if len(order_details) > 0:
            # create order
            order = Order.objects.create(
                customer = customer,
                restaurant_id = request.POST['restaurant_id'],
                total = order_total,
                status = Order.COOKING,
                address = request.POST['address']
            )

            # create order details
            for meal in order_details:
                OrderDetails.objects.create(
                    order = order,
                    meal_id = meal['meal_id'],
                    quantity = meal["quantity"],
                    sub_total = Meal.objects.get(id = meal["meal_id"]).price * meal['quantity']
                )

            return JsonResponse({"status": "success"})


def customer_get_latest_order(request):
    accsess_token = AccessToken.objects.get(token=request.GET.get("access_token"), expires__gt=timezone.now())

    customer = accsess_token.user.customer
    order = OrderSerializer(Order.objects.filter(customer=customer).last()).data

    return JsonResponse({"order": order})

def customer_driver_location(request):
    accsess_token = AccessToken.objects.get(token=request.GET.get("access_token"), expires__gt=timezone.now())

    customer = accsess_token.user.customer

    #Get current location driver(order)
    current_order = Order.objects.filter(customer=customer, status=Order.ONTHEWAY).last()
    location = current_order.driver.locations

    return JsonResponse({"location": location})

##########
#RESTAUANT
##########

def restaurant_order_notification(request, last_request_time):
    notification = Order.objects.filter(restaurant=request.user.restaurant,
                                        created_at__gt=last_request_time).count()
    return JsonResponse({'notification': notification})


##########
#DRIVER
##########

def driver_get_ready_orders(request):
    orders =  OrderSerializer(
        Order.objects.filter(status=Order.READY, driver=None).order_by("-id"),
        many=True
    ).data

    return JsonResponse({"orders":orders})

@csrf_exempt
#POST
# params: access_token, order_id
def driver_pick_order(request):

    if request.method == "POST":
        #Get token
        accsess_token = AccessToken.objects.get(token=request.POST.get("access_token"),
                                                expires__gt=timezone.now())

        #Get Driver
        driver = accsess_token.user.driver

        #Check only order
        if Order.objects.filter(driver=driver).exclude(status=Order.ONTHEWAY):
            return JsonResponse({"status": "failed", "error": "PICK ONLY ONE - !!PIDOR!!"})

        try:
            order = Order.objects.get(
                id = request.POST["order_id"],
                driver = None,
                status = Order.READY
            )
            order.driver = driver
            order.status = Order.ONTHEWAY
            order.picked_at = timezone.now()
            order.save()

            return JsonResponse({"status": "success"})

        except Order.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "This order was picked up by another, LOX"})

    return JsonResponse({})

#Get params: access_token

def driver_get_latest_order(request):
    accsess_token = AccessToken.objects.get(token=request.GET.get("access_token"),
                                            expires__gt=timezone.now())

    driver = accsess_token.user.driver
    order = OrderSerializer(
        Order.objects.filter(driver=driver).order_by("picked_at").last()
    ).data

    return JsonResponse({"order":order})


#Get params: access_token, order_id

@csrf_exempt
def driver_complete_order(request):
    accsess_token = AccessToken.objects.get(token=request.POST.get("access_token"),
                                            expires__gt=timezone.now())

    driver = accsess_token.user.driver

    order = Order.objects.get(id = request.POST["order_id"], driver= driver)
    order.status = Order.DELIVERED
    order.save()

    return JsonResponse({"status": "success"})

#GET access_token
def driver_get_revenue(request):
    accsess_token = AccessToken.objects.get(token=request.GET.get("access_token"),
                                            expires__gt=timezone.now())

    driver = accsess_token.user.driver

    reveneu = {}
    today = timezone.now()
    current_weekdays = [today + timedelta(days=i) for i in range(0 - today.weekday(), 7 - today.weekday())]

    for day in current_weekdays:
        orders = Order.objects.filter(
            driver = driver,
            status = Order.DELIVERED,
            created_at__year = day.year,
            created_at__month = day.month,
            created_at__day = day.day
        )

        reveneu[day.strftime("%a")] = sum(order.total for order in orders)

    return JsonResponse({"revenue": reveneu})


#POST
#access_token, "lat,lng"
@csrf_exempt
def driver_update_location(request):
    if request.method == "POST":
        accsess_token = AccessToken.objects.get(token=request.POST.get("access_token"),
                                                expires__gt=timezone.now())

        driver = accsess_token.user.driver

        #Set location str => database
        driver.locations = request.POST["location"]
        driver.save()

        return JsonResponse({"status": "success"})
