from django.shortcuts import render
from django.views.generic import ListView
from django.views import View


# class HomeView(View):
# 	template_name = 'HomePage.html'
#
# 	def get(self, request):
# 		return render(request, self.template_name, {})

from django.utils import timezone
from django.views.generic.list import ListView

from MelissaTrasporti.models import Fornitore


class FornitoreListView(ListView):
    model = Fornitore
    template_name = 'MelissaTrasporti/Fornitori_list.html'
    context_object_name = 'fornitori_list'
    success_url = "/"
