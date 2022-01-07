from django.contrib import admin
from django.contrib.admin import SimpleListFilter

# Register your models here.
from historicalTesting.models import *


admin.site.register(InstrumentList)
