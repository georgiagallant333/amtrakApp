# from .models import Train
# from rest_framework import viewsets
# from .serializer import TrainSerializer
from .wanderu_scraper import main_scrape
from django.http import JsonResponse

def get_json(request):
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    depart_city = request.GET.get('depart_city', '')
    arrival_city = request.GET.get('arrive_city', '')
    weekdays = request.GET.get('weekdays', '')
    response_list = main_scrape(start_date, end_date, depart_city, arrival_city, weekdays)
    response_dict = {item['_id']: item for item in response_list}
    return JsonResponse(response_dict, safe=True)

