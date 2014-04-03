# coding=utf-8
from django.template.response import TemplateResponse

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class Paginar(object):
    """Decorador que simplifica la paginacion de contenidos. Para que funcione
    la vista debe devolver un TemplateResponse y en el contexto de la response debe
    declarar 'object_list' que contendra una lista de los elementos y el decorador 
    genera en el contexto las variables 'paginator' que contiene las paginas y 'queries'
    que es la url actual de la vista sin el atributo 'page' para que pueda ser usado en los 
    botones anterior, siguiente, etc."""
    def __init__(self, view,
                 per_page='per_page',
                 page='page',
                 object_list='object_list',
                 paginator='paginator',
                 queries='queries'):
        self.DEFAULT_PER_PAGE=10
        self.view = view
        self.per_page = per_page
        self.paginator = paginator
        self.object_list = object_list
        self.page = page
        self.queries = queries

    def __call__(self, request, *args, **kwargs):
        # comportamiento previo a la ejecución de view
        response = self.view(request, *args, **kwargs)
        if response.__class__ != TemplateResponse:
            raise TypeError('La clase de response debe ser TemplateResponse')
        # comportamiento posterior a la ejecución de view
        context = response.context_data
        object_lists = context.get(self.object_list)
        if object_lists:
            per_page = request.GET.get(self.per_page, self.DEFAULT_PER_PAGE)
            page = context[self.page] = request.GET.get(self.page)
            paginator = context[self.paginator] = Paginator(object_lists, per_page)
            try:
                context[self.object_list] = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                context[self.object_list] = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                context[self.object_list] = paginator.page(paginator.num_pages)
            queries_without_page = request.GET.copy()
            if queries_without_page.has_key(self.page):
                del queries_without_page[self.page]
            context[self.queries] = queries_without_page
        return response
