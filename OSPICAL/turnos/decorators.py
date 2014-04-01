# coding=utf-8
from django.template.response import TemplateResponse

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
class Paginar(object):
    def __init__(self, view):
        self.view = view
        self.per_page = 10

    def __call__(self, request, *args, **kwargs):
        # comportamiento previo a la ejecución de view
        response = self.view(request, *args, **kwargs)
        if response.__class__ != TemplateResponse:
            raise TypeError('La clase de response debe ser TemplateResponse')
        # comportamiento posterior a la ejecución de view
        context = response.context_data
        object_lists = context['object_list']
        page = context['page'] = request.GET.get('page')
        paginator = context['paginator'] = Paginator(object_lists, self.per_page) # Show 25 contacts per page
        try:
            context['object_list'] = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            context['object_list'] = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            context['object_list'] = paginator.page(paginator.num_pages)
        queries_without_page = request.GET.copy()
        if queries_without_page.has_key('page'):
            del queries_without_page['page']
        context['queries'] = queries_without_page
        return response