from django.db import models
from django import forms
import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geospatialproject.settings")

INSECT_CHOICES = (
    ('Jack Pine Budworm','Jack Pine Budworm'),
    ('Spruce Budworm', 'Spruce Budworm'),
)

DAMAGE_CHOICES = (
    ('Light','Light'),
    ('Moderate-Severe', 'Moderate-Severe'),
    ('Mortality', 'Mortality'),
)

class ASM(models.Model):
    insect = models.CharField(max_length=50,choices = INSECT_CHOICES, default='Jack Pine Budworm')
    dtype = models.CharField(max_length=50,choices = DAMAGE_CHOICES,default='Mortality')
    year = models.IntegerField(default=2018)

class ASM_Geom(models.Model):
    asm_geom = models.CharField(max_length=50000,default='PlaceHolder')

SPEC_CHOICES = (
    ('Jack Pine','Jack Pine'),
    ('Balsam Fir', 'Balsam Fir'),
    ('White Spruce', 'White Spruce'),
    ('Black Spruce', 'Black Spruce'),
    ('All SBW Host Species', 'All SBW Host Species'),
)

DSET_CHOICES = (
    ('Beaudoin','Beaudoin'),
)

class SPEC(models.Model):
    threshold = models.IntegerField()
    
    dset = models.CharField(max_length=50,choices = DSET_CHOICES,default='Beaudoin')
    hspecies = models.CharField(max_length=50,choices = SPEC_CHOICES,default='Jack Pine')


class AGE(models.Model):
    age = models.IntegerField(default=30)
    dset2 = models.CharField(max_length=50,choices = DSET_CHOICES,default='Beaudoin')

class GEOM(models.Model):
    geometry = models.CharField(max_length=50000,default='PlaceHolder')

class FILTER(models.Model):
    year1 = models.IntegerField(default=2009)
    year2 = models.IntegerField(default=2021)
    area = models.FloatField(default=0.0324)
    droad = models.FloatField(default=1)

class GEOM2(models.Model):
    geometry2 = models.CharField(max_length=50000,default='PlaceHolder')

class EXPORT(models.Model):
    nsite = models.IntegerField(default=5)
    
class FORCE(models.Model):
    action = models.CharField(max_length=10,default='No')
