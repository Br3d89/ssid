from django.shortcuts import render
import random
import this
# Create your views here.
from django.test import TestCase

# Create your tests here.

text = ''.join([this.d.get(c,c) for c in this.s])
title, _, *quotes = text.splitlines()

def index(request):
    return render(request, 'index.html', {'title':title,'quote':random.choice(quotes)})