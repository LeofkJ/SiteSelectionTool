from django import forms
from .models import ASM
from .models import SPEC
from .models import AGE
from .models import FILTER
from .models import GEOM
from .models import GEOM2
from .models import EXPORT
from .models import FORCE
import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geospatialproject.settings")


def test_form(request):
     b=request.POST.get('insect')
     r = request.POST.get('dtype')
     y = request.POST.get('year')

     class Meta:
          model = ASM
          fields = ('insect','dtype','year',)
     return b,r,y

class HomeForm(forms.ModelForm):
    insect = forms.CharField()
    dtype = forms.CharField()
    year = forms.IntegerField()

    class Meta:
        model = ASM
        fields = ('insect','dtype','year',)

def test_form2(request):
     b=request.POST.get('hspecies')
     r = request.POST.get('threshold')
     y = request.POST.get('dset')

     class Meta:
          model = SPEC
          fields = ('hspecies','threshold','dset',)
     return b,r,y

class HomeForm2(forms.ModelForm):
    hspecies = forms.CharField()
    threshold = forms.IntegerField()
    dset = forms.CharField()

    class Meta:
        model = SPEC
        fields = ('hspecies','threshold','dset',)

def test_form3(request):
     b=request.POST.get('age')
     r = request.POST.get('dset2')

     class Meta:
          model = AGE
          fields = ('age','dset2',)
     return b,r

class HomeForm3(forms.ModelForm):
    age = forms.IntegerField()
    dset2 = forms.CharField()

    class Meta:
        model = AGE
        fields = ('age','dset2',)


def test_form4(request):
     y1=request.POST.get('year1')
     y2= request.POST.get('year2')
     area = request.POST.get('area')
     droad = request.POST.get('droad')

     class Meta:
          model = FILTER
          fields = ('year1','year2','area','droad',)
     return y1,y2,area,droad

class HomeForm4(forms.ModelForm):
    year1 = forms.IntegerField()
    year2 = forms.IntegerField()
    area = forms.FloatField()
    droad = forms.FloatField()

    class Meta:
        model = FILTER
        fields = ('year1','year2','area','droad',)

def test_geom(request):
     g=request.POST.get('geometry')

     class Meta:
          model = GEOM
          fields = ('geometry',)
     return g

class HomeFormGeom(forms.ModelForm):
    geometry = forms.CharField()

    class Meta:
        model = GEOM
        fields = ('geometry',)

def test_geom2(request):
     g=request.POST.get('geometry2')

     class Meta:
          model = GEOM2
          fields = ('geometry2',)
     return g

class HomeFormGeom2(forms.ModelForm):
    geometry2 = forms.CharField()

    class Meta:
        model = GEOM2
        fields = ('geometry2',)

def test_form5(request):
     e=request.POST.get('nsite')

     class Meta:
          model = EXPORT
          fields = ('nsite',)
     return e

class HomeForm5(forms.ModelForm):
    etype = forms.IntegerField()

    class Meta:
        model = EXPORT
        fields = ('nsite',)

def test_form6(request):
     e=request.POST.get('action')

     class Meta:
          model = FORCE
          fields = ('action',)
     return e

class HomeForm6(forms.ModelForm):
    action = forms.CharField()

    class Meta:
        model = FORCE
        fields = ('action',)
