from django.http import JsonResponse

import json
from oauth2_provider.models import AccessToken
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from foodtaskerapp.models import Restaurant
from foodtaskerapp.models import Meal
from foodtaskerapp.models import Order
from foodtaskerapp.models import OrderDetails
from foodtaskerapp.serializer import RestaurantSerializer
from foodtaskerapp.serializer import MealSerializer


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
    return JsonResponse({})


def restaurant_order_notification(arg):
    return JsonResponse({})