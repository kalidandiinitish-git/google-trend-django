from django.shortcuts import render
from django.http import JsonResponse
from .trends_engine import get_trends, get_regions, get_related, get_compare, get_status, get_multi, get_summary


def index(request):
    return render(request, 'analyzer/index.html')


def api_status(request):
    return JsonResponse(get_status())


def api_trends(request):
    keyword   = request.GET.get('keyword', 'Python').strip()
    timeframe = request.GET.get('timeframe', 'today 12-m')
    return JsonResponse(get_trends(keyword, timeframe))


def api_regions(request):
    keyword   = request.GET.get('keyword', 'Python').strip()
    timeframe = request.GET.get('timeframe', 'today 12-m')
    return JsonResponse(get_regions(keyword, timeframe))


def api_related(request):
    keyword   = request.GET.get('keyword', 'Python').strip()
    timeframe = request.GET.get('timeframe', 'today 12-m')
    return JsonResponse(get_related(keyword, timeframe))


def api_compare(request):
    kw1       = request.GET.get('kw1', 'Python').strip()
    kw2       = request.GET.get('kw2', 'JavaScript').strip()
    timeframe = request.GET.get('timeframe', 'today 12-m')
    return JsonResponse(get_compare(kw1, kw2, timeframe))


def api_multi(request):
    raw       = request.GET.get('keywords', '').strip()
    timeframe = request.GET.get('timeframe', 'today 12-m')
    keywords  = [k.strip() for k in raw.split(',') if k.strip()]
    if not keywords:
        return JsonResponse({"error": "Please provide comma-separated keywords."})
    return JsonResponse(get_multi(keywords, timeframe))


def api_summary(request):
    keyword   = request.GET.get('keyword', 'Python').strip()
    timeframe = request.GET.get('timeframe', 'today 12-m')
    return JsonResponse(get_summary(keyword, timeframe))
