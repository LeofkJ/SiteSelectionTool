from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.utils.encoding import smart_str
import folium
import geopandas as gpd
import pandas as pd
from ortools.linear_solver import pywraplp
import math
import os
from .forms import test_form
from .forms import HomeForm
from .forms import test_form2
from .forms import HomeForm2
from .forms import test_form3
from .forms import HomeForm3
from .forms import test_form4
from .forms import HomeForm4
from .forms import test_form5
from .forms import HomeForm5
from .forms import test_form6
from .forms import HomeForm6
from .models import ASM
from .models import SPEC
from .models import AGE
from .models import FILTER
from .models import GEOM
from .models import GEOM2
from .models import ASM_Geom
from .models import EXPORT
from .models import FORCE
import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geospatialproject.settings")

# Create your views here.


def read_data(fp):

    jack_pine_abundance = gpd.read_file(fp)
    return jack_pine_abundance

def get_dist_haversine_polygon(gdf1):
    pdf1 = gdf1.centroid
    pdf2 = gdf1.centroid
    gdf1['id_num'] = list(range(0,len(gdf1)))
    print(gdf1)
    site_options = {} 
    for x,y,id_num in zip(pdf1.x,pdf1.y,gdf1['id_num']):
        
        df = pd.DataFrame() 
        dist_list = [] 
        lon_list = [] 
        lat_list = []
        id_list = []
        for x2,y2,id_num2 in zip(pdf2.x,pdf2.y,gdf1['id_num']): 
            if (x,y,) != (x2,y2): 

                lon1 = math.radians(x)
                lat1 = math.radians(y)
                lon2 = math.radians(x2)
                lat2 = math.radians(y2) 

                # haversine formula 
                dlon = lon2 - lon1 
                dlat = lat2 - lat1 
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.asin(math.sqrt(a)) 
                r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
                dist = c * r
                dist_list.append(dist)
                lon_list.append(x2)
                lat_list.append(y2)
                id_list.append(id_num2)

        df['polyid'] = id_list 
        df['dist'] = dist_list
        df['lon'] = lon_list
        df['lat'] = lat_list
        site_options[(x,y,)] = df

    return site_options


def optimize_for_site(site,dictionary_list,e):

    information = pd.DataFrame()
    store_pot_site = [] 
    for dictionary in dictionary_list:

        pot_site = dictionary[site].reset_index(drop=True)
        store_pot_site.append(pot_site)

    #print(store_pot_site)
    solver = pywraplp.Solver.CreateSolver('SCIP')

    var_list = []
    dist_list = [] 
    lon_list = [] 
    lat_list = [] 
    var_list_sites = {}
    id_list= [] 

    count = 0
    checkpoints = list(range(1,len(store_pot_site)+1))
    
    for list_ in store_pot_site:
        
        storage = [] 
        count+=1 
        count2 = 0 #count 2 is the site index 
        for inst in list_.iterrows(): 
            inst = list(inst)[1]
            var_list.append('x'+str(count)+'_'+str(count2))
            dist_list.append(inst['dist'])
            lon_list.append(inst['lon'])
            lat_list.append(inst['lat'])
            id_list.append(inst['polyid'])
            
            storage.append('x'+str(count)+'_'+str(count2))
            count2+=1 

        var_list_sites[count] = storage
    

    var_collect = {}


    merge_list = [j for i in var_list_sites.values() for j in i]
    
    for i in range(0, len(var_list)): 
        # solver.IntVar(0.0, 1, var_list[i]) --> tell computer that the variable can
        # only be 1 or 0. 
        var_collect[var_list[i]] = solver.IntVar(0.0, 1, var_list[i])

                
    information['variable'] = var_list #merge_list
    
    information['distance'] = dist_list 
    information['lat'] = lat_list
    information['lon'] = lon_list
    information['id_num'] = id_list 

    locals().update(var_collect)
    globals().update(var_collect)
    append_lists = []

    for var in var_list_sites.values(): 
        all_vars = [eval(i) for i in var]
        append_lists.append(all_vars)

    for list_of_con in append_lists:
        
        solver.Add(sum(list_of_con) == e)

    #print('Number of constraints =', solver.NumConstraints()) 
    #print('Number of variables =', solver.NumVariables())

    #Tell computer that each component of the objective function is dist * variable
    concat_list = [j for i in append_lists for j in i]
    
    obj_collect = [i*j for i, j in zip(concat_list,dist_list)]
    #Tell the computer to maximize the sum of these volume*variable pairs 
    solver.Minimize(sum(obj_collect))

    #Solve 
    status = solver.Solve()

    #Get information from solver 
    decision = [] 
    if status == pywraplp.Solver.OPTIMAL:
        
        #print('Objective value =', solver.Objective().Value())
        for var in concat_list: 
          #Append to decision list the solution for the specific variable. 
          decision.append(abs(var.solution_value()))
    else:
        print('The problem does not have an optimal solution.')

    if len(decision) > 0: 
      #Append a row to the original table IF there is an optimal solution
      information['visit'] = decision 

      #Here's our table. 'cut' tells us whether to harvest or not. 
      #print(information[information['visit'] == 1])
    
    information = information[information['visit'] == 1]

    
    return float(solver.Objective().Value()),information
      

def index(request):

    #form = HomeForm(request.POST)
    #if form.is_valid():
         #form.save()

    b,r,y = test_form(request)
    form = HomeForm(request.POST)

    if form.is_valid():
        
        try:
            b = str(b)
            r = str(r)
            y = int(y)
        except:
            b=-1
            r=-1
            y=-1

    if b != -1 and b is not None:
        try: 
            inst_ini = ASM.objects.get(id=1)
        except:
            if y is not None: 
                inst = ASM.objects.create(insect=b,dtype=r,year=y)
                inst_ini = ASM.objects.get(id=1)
            else:
                inst = ASM.objects.create(insect='Jack Pine Budworm',dtype='Mortality',year=2018)
                inst_ini = ASM.objects.get(id=1)          

        if inst_ini == None: 
        
            inst_ini = ASM.objects.create(insect=b,dtype=r,year=y)

        else:

            inst_ini.insect = b

            inst_ini.dtype = r

            inst_ini.year = y
            inst_ini.save(update_fields=['insect','dtype','year'])
    

    key = 'pk.eyJ1IjoiY2xhcmFyaXNrIiwiYSI6ImNrbjk5cGxoMjE1cHIydm4xNW55cmZ1cXgifQ.3CXp0GaWY1S7iMcPP8n9Iw'
    tile_input = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(key)

        
        

    m = folium.Map(location=[48.63290858589535,-83.671875],zoom_start=5,control_scale=True,tiles=tile_input,attr='Mapbox',API_key = key,prefer_canvas=True)
    d = 0
    df = gpd.GeoDataFrame()
    print(b)
    if b == 'Jack Pine Budworm' or b == 'Spruce Budworm':
         print('ok')
         if b == 'Jack Pine Budworm':
             df = read_data('all_jpb_website_s2_fix.geojson')
         if b == 'Spruce Budworm':
             df = read_data('sbw_005_fix_correct.geojson')
             print(df)
             
         df = df[df['RANKING'] == r]
         df = df[df['EVENT_YEAR'] == y]
         d = len(df)

         df_save = df.dissolve()
         df_save = df_save['geometry']

         try: 
             inst_ini = ASM_Geom.objects.get(id=1)
         except:
             inst_ini = None
         if inst_ini == None and len(df_save) > 0:         
             inst = ASM_Geom.objects.create(asm_geom=str(df_save[0]))
        
         elif len(df_save) < 0:
             inst_ini = None
         else:
            inst_ini.asm_geom = str(df_save)
            inst_ini.save(update_fields=['asm_geom'])
         
         for _, r in df.iterrows():

              sim_geo = gpd.GeoSeries(r['geometry']).simplify(tolerance=1)
              geo_j = sim_geo.to_json()
              geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'green','color': 'green'})
              geo_j.add_to(m)
    m = m._repr_html_() #HTML representation of original m
    context = {

        'm': m,
        'd': d,

        }

    return render(request,'index.html',context)
     
def map(request):
    #make try except in case they go to this tab first
    #Get year damage
    field_name = 'year'
    obj = ASM.objects.first()
    field_object = ASM._meta.get_field(field_name)
    y = field_object.value_from_object(obj)
    print(y)
    
    #Get insect type
    field_name = 'insect'
    obj = ASM.objects.first()
    field_object = ASM._meta.get_field(field_name)
    #field_object = Post._meta.get_field(field_name)
    b = field_object.value_from_object(obj)
    #b = obj
    print(b)

    #Get dtype
    field_name = 'dtype'
    obj = ASM.objects.first()
    field_object = ASM._meta.get_field(field_name)
    r = field_object.value_from_object(obj)
    print(r)

    #Get dtype
    field_name = 'asm_geom'
    obj = ASM_Geom.objects.first()
    field_object = ASM_Geom._meta.get_field(field_name)
    geom = field_object.value_from_object(obj)
    print(geom)

    from shapely import wkt

    d2 = wkt.loads(geom)

    gdf = gpd.GeoDataFrame(geometry=[d2], crs='epsg:4326')

    print('check1') 
    h,t,d = test_form2(request)
    print('check2')
    print(t)

    if t is not None:
        print('check4')
        h = str(h)
        d = str(d)
        t = int(t)
    else:
        print('check3') 
        h = -1
        d = -1
        t = -1
              

    if t != -1:
        print('check!')
        try:

            from django.db import connection
            tables = connection.introspection.table_names()
            seen_models = connection.introspection.installed_models(tables)
            from django.contrib import admin
            admin.site.register(SPEC)
            print(seen_models)
            inst = SPEC.objects.create(threshold=t,hspecies=h,dset=d)
            inst_ini = SPEC.objects.get(id=1)
        except: 
            if t is not None: 
                inst = SPEC.objects.create(threshold=t,hspecies=h,dset=d)
                inst_ini = SPEC.objects.get(id=1)
            else:
                inst = SPEC.objects.create(threshold=30,hspecies='Jack Pine',dset='Beaudoin')
                inst_ini = SPEC.objects.get(id=1) 
        if inst_ini == None: 
        
            inst_ini = SPEC.objects.create(threshold=t,hspecies=h,dset=d)

        else:

            inst_ini.threshold = t

            inst_ini.hspecies = h

            inst_ini.dset = d
            inst_ini.save(update_fields=['threshold','hspecies','dset'])        
        

    key = 'pk.eyJ1IjoiY2xhcmFyaXNrIiwiYSI6ImNrbjk5cGxoMjE1cHIydm4xNW55cmZ1cXgifQ.3CXp0GaWY1S7iMcPP8n9Iw'
    tile_input = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(key)


    m = folium.Map(location=[48.63290858589535,-83.671875],zoom_start=5,control_scale=True,tiles=tile_input,attr='Mapbox',API_key = key,prefer_canvas=True)
    d = 0
    df = gpd.GeoDataFrame()
    if h == 'Jack Pine':
         

         if h != -1:

             df2 = read_data('jack_pine/spec_'+str(round(t, -1))+'.geojson')

             #df2 = df2[df2['ROUND2'] >= t]
             print('check6')
             df2['dissolvefield'] = [1]*len(df2)
             df2 = df2.dissolve(by='dissolvefield').dissolve()
             df2 = df2.intersection(gdf['geometry'])
            
             d = len(df2)
             sim_geo = gpd.GeoSeries(df2).simplify(tolerance=1)
             geo_j = sim_geo.to_json()
             geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'blue','color': 'blue'})
             geo_j.add_to(m)
         else:
             df2 = gpd.GeoDataFrame()

    if h == 'Balsam Fir':
         

         if t != -1:
             bf_op = [20,30,40,50,60]
             
             closest = [abs(t-x) for x in bf_op].index(min([abs(t-x) for x in bf_op]))
             if min([abs(t-x) for x in bf_op]) > 10 and t > max(bf_op):
                 df2 = gpd.GeoDataFrame()
             else:
                 df2 = read_data('balsam_fir/spec_bf_'+str(bf_op[closest])+'.geojson')
                 print(df2)
            
             #df2 = df2[df2['ROUND2'] >= t]
             print('check6')
             #df2['dissolvefield'] = [1]*len(df2)
             #df2 = df2.dissolve(by='dissolvefield').dissolve()
             df2 = df2.intersection(gdf['geometry'])
             print(df2)
            
             d = len(df2)
             sim_geo = gpd.GeoSeries(df2).simplify(tolerance=1)
             geo_j = sim_geo.to_json()
             geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'blue','color': 'blue'})
             geo_j.add_to(m)
         else:
             df2 = gpd.GeoDataFrame()

    if h == 'White Spruce':
         

         if t != -1:
             sw_op = [10,20,30,40,50]
             closest = [abs(t-x) for x in sw_op].index(min([abs(t-x) for x in sw_op]))
             print(str(sw_op[closest]))
             if min([abs(t-x) for x in sw_op]) > 10 and t > max(sw_op):
                 df2 = gpd.GeoDataFrame()
             else:
                 df2 = read_data('white_spruce/spec_sw_'+str(sw_op[closest])+'.geojson')
                 print(df2)
            
             #df2 = df2[df2['ROUND2'] >= t]
             print('check6')
             #df2['dissolvefield'] = [1]*len(df2)
             #df2 = df2.dissolve(by='dissolvefield').dissolve()
             df2 = df2.intersection(gdf['geometry'])
             print(df2)
            
             d = len(df2)
             sim_geo = gpd.GeoSeries(df2).simplify(tolerance=1)
             geo_j = sim_geo.to_json()
             geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'blue','color': 'blue'})
             geo_j.add_to(m)
         else:
             df2 = gpd.GeoDataFrame()

    if h == 'Black Spruce':
         

         if t != -1:
             sb_op = [40,50,60,70,80,90,100]
             closest = [abs(t-x) for x in sb_op].index(min([abs(t-x) for x in sb_op]))
             print(str(sb_op[closest]))
             if min([abs(t-x) for x in sb_op]) > 10 and t > max(sb_op):
                 df2 = gpd.GeoDataFrame()
             else:
                 df2 = read_data('black_spruce/spec_sb_'+str(sb_op[closest])+'.geojson')

             #df2 = df2[df2['ROUND2'] >= t]
             print('check6')
             #df2['dissolvefield'] = [1]*len(df2)
             #df2 = df2.dissolve(by='dissolvefield').dissolve()
             df2 = df2.intersection(gdf['geometry'])
             print(df2)
            
             d = len(df2)
             sim_geo = gpd.GeoSeries(df2).simplify(tolerance=1)
             geo_j = sim_geo.to_json()
             geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'blue','color': 'blue'})
             geo_j.add_to(m)
         else:
             df2 = gpd.GeoDataFrame()

    
    if h == 'All SBW Host Species':
        
         if t != -1:
             sb_op = [30,40,50,60,70,80,90,100]
             closest = [abs(t-x) for x in sb_op].index(min([abs(t-x) for x in sb_op]))
             print(str(sb_op[closest]))
             if min([abs(t-x) for x in sb_op]) > 10 and t > max(sb_op):
                 df2 = gpd.GeoDataFrame()
             else:
                 df2 = read_data('all_host/spec_all_'+str(sb_op[closest])+'.geojson')

             #df2 = df2[df2['ROUND2'] >= t]
             print('check6')
             #df2['dissolvefield'] = [1]*len(df2)
             #df2 = df2.dissolve(by='dissolvefield').dissolve()
             df2 = df2.intersection(gdf['geometry'])
             print(df2)
            
             d = len(df2)
             sim_geo = gpd.GeoSeries(df2).simplify(tolerance=1)
             geo_j = sim_geo.to_json()
             geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'blue','color': 'blue'})
             geo_j.add_to(m)
         else:
             df2 = gpd.GeoDataFrame()        

    m = m._repr_html_() #HTML representation of original m
    context = {

        'm': m,
        'd': d,

        }

    return render(request,'map.html',context)


def map2(request):
    #make try except in case they go to this tab first
    #Get year damage
    field_name = 'year'
    obj = ASM.objects.first()
    field_object = ASM._meta.get_field(field_name)
    y = field_object.value_from_object(obj)
    print(y)
    
    #Get insect type
    field_name = 'insect'
    obj = ASM.objects.first()
    field_object = ASM._meta.get_field(field_name)
    #field_object = Post._meta.get_field(field_name)
    b = field_object.value_from_object(obj)
    #b = obj
    print(b)

    #Get dtype
    field_name = 'dtype'
    obj = ASM.objects.first()
    field_object = ASM._meta.get_field(field_name)
    r = field_object.value_from_object(obj)
    print(r)

    #Get dtype
    field_name = 'asm_geom'
    obj = ASM_Geom.objects.first()
    field_object = ASM_Geom._meta.get_field(field_name)
    geom = field_object.value_from_object(obj)

    from shapely import wkt

    d2 = wkt.loads(geom)

    gdf = gpd.GeoDataFrame(geometry=[d2], crs='epsg:4326')

    print('check1') 
    a,d = test_form3(request)
    print('check2')
    print(a)

    if a is not None:
        print('check4')
        a = int(a)
        d = str(d)
    else:
        print('check3') 
        a = -1
        d = -1
              

    if a != -1:
        print('check!')
        try:
            inst = AGE.objects.create(age=a,dset2=d)
            inst_ini = AGE.objects.get(id=1)
        except: 
            if a is not None: 
                inst = AGE.objects.create(age=a,dset2=d)
                inst_ini = AGE.objects.get(id=1)
            else:
                inst = AGE.objects.create(age=30,dset2='Beaudoin')
                inst_ini = AGE.objects.get(id=1) 
        if inst_ini == None: 
        
            inst_ini = AGE.objects.create(age=a,dset2=d)

        else:

            inst_ini.insect = b

            inst_ini.dtype = r

            inst_ini.year = y
            inst_ini.save(update_fields=['age','dset2'])        
        

    key = 'pk.eyJ1IjoiY2xhcmFyaXNrIiwiYSI6ImNrbjk5cGxoMjE1cHIydm4xNW55cmZ1cXgifQ.3CXp0GaWY1S7iMcPP8n9Iw'
    tile_input = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(key)


    m = folium.Map(location=[48.63290858589535,-83.671875],zoom_start=5,control_scale=True,tiles=tile_input,attr='Mapbox',API_key = key,prefer_canvas=True)
    d = 0
    df = gpd.GeoDataFrame()
    if b == 'Jack Pine Budworm':
         

         if a != -1:

             a = round(a,-1)
             print(a)

             if a in [160, 130, 100, 70, 140, 110, 80, 50, 150, 120, 90, 60]:
                 print(a)
                 df2 = read_data('age/age_'+str(a)+'.geojson')
            
             else:
                 #get closest number in list
                 minus = [x-a for x in [160, 130, 100, 70, 140, 110, 80, 50, 150, 120, 90, 60]]
                 print(minus)
                 get_min = min(minus)
                 a = get_min
                 print(a)
                 df2 = read_data('age/age_'+str(a)+'.geojson')

             print('check6')
             df2['dissolvefield'] = [1]*len(df2)
             df2 = df2.dissolve(by='dissolvefield').dissolve()
             print(df2)
             df2 = df2.intersection(gdf['geometry'].unary_union)
             
            
             d = len(df2)
             sim_geo = gpd.GeoSeries(df2).simplify(tolerance=1)
             geo_j = sim_geo.to_json()
             geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'yellow','color': 'yellow'})
             geo_j.add_to(m)
                 

         else:

             df2 = gpd.GeoDataFrame()  
        
    if b == 'Spruce Budworm':
         

         if a != -1:

             a = round(a,-1)
             print(a)

             if a in [50,60,70,80,90,100,110,120,130,140,150,160,170,180]:
                 print(a)
                 df2 = read_data('age_sbw/age_sbw_'+str(a)+'.geojson')
            
             else:
                 #get closest number in list
                 minus = [x-a for x in [50,60,70,80,90,100,110,120,130,140,150,160,170,180]]
                 print(minus)
                 get_min = min(minus)
                 a = get_min
                 print(a)
                 df2 = read_data('age_sbw/age_sbw_'+str(a)+'.geojson')

             print('check6')
             df2['dissolvefield'] = [1]*len(df2)
             df2 = df2.dissolve(by='dissolvefield').dissolve()
             print(df2)
             df2 = df2.intersection(gdf['geometry'].unary_union)
             
            
             d = len(df2)
             sim_geo = gpd.GeoSeries(df2).simplify(tolerance=1)
             geo_j = sim_geo.to_json()
             geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'yellow','color': 'yellow'})
             geo_j.add_to(m)
                 

         else:

             df2 = gpd.GeoDataFrame() 
    m = m._repr_html_() #HTML representation of original m
    context = {

        'm': m,
        'd': d,

        }

    return render(request,'map2.html',context)

def map3(request):

    field_name = 'threshold'
    obj = SPEC.objects.first()
    field_object = SPEC._meta.get_field(field_name)
    t = field_object.value_from_object(obj)
    
    #Get insect type
    field_name = 'hspecies'
    obj = SPEC.objects.first()
    field_object = SPEC._meta.get_field(field_name)
    hspecies = field_object.value_from_object(obj)

    #Get dtype
    field_name = 'dset'
    obj = SPEC.objects.first()
    field_object = SPEC._meta.get_field(field_name)
    d = field_object.value_from_object(obj)


    field_name = 'age'
    obj = AGE.objects.first()
    field_object = AGE._meta.get_field(field_name)
    a = field_object.value_from_object(obj)
    
    #Get insect type
    field_name = 'dset2'
    obj = AGE.objects.first()
    field_object = AGE._meta.get_field(field_name)
    d2 = field_object.value_from_object(obj)
    
    #Get dtype
    field_name = 'asm_geom'
    obj = ASM_Geom.objects.first()
    field_object = ASM_Geom._meta.get_field(field_name)
    geom = field_object.value_from_object(obj)
    print('obtain from database') 

    from shapely import wkt

    d2 = wkt.loads(geom)

    gdf = gpd.GeoDataFrame(geometry=[d2], crs='epsg:4326')

    key = 'pk.eyJ1IjoiY2xhcmFyaXNrIiwiYSI6ImNrbjk5cGxoMjE1cHIydm4xNW55cmZ1cXgifQ.3CXp0GaWY1S7iMcPP8n9Iw'
    tile_input = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(key)


    m = folium.Map(location=[48.63290858589535,-83.671875],zoom_start=5,control_scale=True,tiles=tile_input,attr='Mapbox',API_key = key,prefer_canvas=True)

    d = 0


    if a != -1:

     a = round(a,-1)

     if a in [160, 130, 100, 70, 40, 10, 140, 110, 80, 50, 20, 150, 120, 90, 60, 30]:
         df2 = read_data('age/age_'+str(a)+'.geojson')

     else:
         #get closest number in list
         minus = [x-a for x in [160, 130, 100, 70, 40, 10, 140, 110, 80, 50, 20, 150, 120, 90, 60, 30]]
         get_min = min(minus)
         a = get_min
         df2 = read_data('age/age_'+str(a)+'.geojson')

     df2['dissolvefield'] = [1]*len(df2)
     df2 = df2.dissolve(by='dissolvefield').dissolve() #.unary_union
     
     print('Age complete') 


    if t != -1:
        if hspecies == 'Jack Pine': 
            df3 = read_data('jack_pine/spec_'+str(round(t, -1))+'.geojson')
        if hspecies == 'Balsam Fir':
             bf_op = [20,30,40,50,60]
             closest = [abs(t-x) for x in bf_op].index(min([abs(t-x) for x in bf_op]))
             print(str(bf_op[closest]))
             if min([abs(t-x) for x in bf_op]) > 10 and t > max(bf_op):
                 df3 = gpd.GeoDataFrame() 
             else: 
                 df3 = read_data('balsam_fir/spec_bf_'+str(bf_op[closest])+'.geojson')
                 print(df3)            
            
        if hspecies == 'White Spruce':

             sw_op = [10,20,30,40,50]
             closest = [abs(t-x) for x in sw_op].index(min([abs(t-x) for x in sw_op]))
             print(str(sw_op[closest]))
             if min([abs(t-x) for x in sw_op]) > 10 and t > max(sw_op):
                 df3 = gpd.GeoDataFrame()
             else:
                 df3 = read_data('white_spruce/spec_sw_'+str(sw_op[closest])+'.geojson')
                 print(df3)
        if hspecies == 'Black Spruce':
            
            sb_op = [40,50,60,70,80,90,100]
            closest = [abs(t-x) for x in sb_op].index(min([abs(t-x) for x in sb_op]))
            print(str(sb_op[closest]))
            if min([abs(t-x) for x in sb_op]) > 10 and t > max(sb_op):
                df3 = gpd.GeoDataFrame()
            else: 
                df3 = read_data('black_spruce/spec_sb_'+str(sw_op[closest])+'.geojson')
            
            
        print('check9')
        df3['dissolvefield'] = [1]*len(df3)
        df3 = df3.dissolve(by='dissolvefield').dissolve()
        df3 = df3.intersection(gdf['geometry'])
        print(df3)
    else:
        df3 = gpd.GeoDataFrame() 

    print('check7')
    print(df3[0].is_empty)
    if not df3[0].is_empty:
        print(df3)
        df4 = df2.clip(df3.unary_union)
        print(df4)
        

        df4 = gpd.GeoDataFrame(geometry=df4['geometry'])
        df4['dissolvefield'] = 1
        df4 = df4.dissolve(by='dissolvefield').dissolve()
        #print(df4)

        
        df5 = df4 #df4.intersection(gdf['geometry'].unary_union) #intersection

        print(df5)
        df5 = gpd.GeoDataFrame(geometry=df5['geometry'])
        df5['dissolvefield'] = 1
        #print(df5)
        df5 = df5.dissolve(by='dissolvefield').dissolve()

        #print(df5['geometry'])

        dinput = str(df5['geometry'])
        print(dinput)

        #df5 = gpd.GeoDataFrame(geometry=df5)

        try:
            inst_ini = GEOM.objects.get(id=1)
        except:
            inst_ini = None
        if inst_ini == None:         
            inst = GEOM.objects.create(geometry=dinput)

        else:
            inst_ini.geometry = dinput
            inst_ini.save(update_fields=['geometry'])               

        if len(df5) > 1: 
            for _, r in df5.iterrows():
                sim_geo = gpd.GeoSeries(r['geometry']) #.simplify(tolerance=1)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'green','fill_opacity':0.8,'color': 'green'})
                geo_j.add_to(m)
        elif len(df5) == 0:
            print('No polygons selected') 
        else:
            sim_geo = gpd.GeoSeries(df5['geometry'])
            geo_j = sim_geo.to_json()
            geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'green','fill_opacity':0.8,'color': 'green'})
            geo_j.add_to(m)             
             
    m = m._repr_html_() #HTML representation of original m
    context = {

        'm': m,
        'd': d,

        }

    return render(request,'map3.html',context)


    
def map4(request):

    #Get insect type
    field_name = 'geometry'
    obj = GEOM.objects.first()
    field_object = GEOM._meta.get_field(field_name)
    d2 = field_object.value_from_object(obj)
    print(d2)

    from shapely import wkt

    d2 = wkt.loads(d2)

    gdf = gpd.GeoDataFrame(geometry=[d2], crs='epsg:4326')

    y1,y2,a,dr = test_form4(request)

    print(a)

    if y1 is not None and y2 is not None and a is not None:
        print('check4')
        y1 = int(y1)
        y2 = int(y2)
        a = float(a)
        dr = float(dr)
    else:
        print('check3') 
        y1 = -1
        y2 = -1
        a = -1
        dr = -1 

    key = 'pk.eyJ1IjoiY2xhcmFyaXNrIiwiYSI6ImNrbjk5cGxoMjE1cHIydm4xNW55cmZ1cXgifQ.3CXp0GaWY1S7iMcPP8n9Iw'
    tile_input = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(key)

        
        

    m = folium.Map(location=[48.63290858589535,-83.671875],zoom_start=5,control_scale=True,tiles=tile_input,attr='Mapbox',API_key = key,prefer_canvas=True)
    d = 0
    df = gpd.GeoDataFrame()
    if y1 != -1:
         df = read_data('fires_flat.geojson')

         df = df[df['YEAR'] >= y1]
         df = df[df['YEAR'] <= y2]

         df = df.dissolve() 

         print(df)

         r = gdf.difference(df['geometry'])
         r = r.geometry.explode()
         r = gpd.GeoDataFrame(geometry=r).to_crs('esri:102001')
            

         if dr > 0:

             roads = read_data('mroads_simple.geojson').to_crs('esri:102001')

             buff = roads.geometry.buffer(dr*1000).unary_union

             #buffer_df = gpd.GeoDataFrame(geometry=buff, crs='esri:102001')
             #buffer_df['dissolvefield'] = [1]*len(buff)
             #buff = buffer_df

             if_intersect = r.intersects(buff) 

             r['if_intersect'] = list(if_intersect) 

             r = r[r['if_intersect'] == True]
               

         r = gpd.GeoDataFrame(r,geometry=r['geometry'])
         r['area'] = r['geometry'].area/ 10**6
         print(r)
         r = r[r['area'] >= a]

         print(r)
         if len(r) > 0: 
             r = gpd.GeoDataFrame(geometry=r['geometry']).dissolve()
             r = r.to_crs('EPSG:4326')

             r = r['geometry']
         else:
             r = r
         try: 
             inst_ini = GEOM2.objects.get(id=1)
         except:
             inst_ini = None
         if inst_ini == None:         
             inst = GEOM2.objects.create(geometry2=str(r[0]))
            
         else:
             if len(r) > 0: 
                 inst_ini.geometry2 = str(r[0])
                 inst_ini.save(update_fields=['geometry2'])
                 
             else:
                 inst_ini.geometry2 = 'None'
                 inst_ini.save(update_fields=['geometry2'])
         if len(r) > 0: 
             sim_geo = gpd.GeoSeries(r) #.simplify(tolerance=1)
             geo_j = sim_geo.to_json()
             geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': 'green','fill_opacity':0.8,'color': 'green'})
             geo_j.add_to(m)

             sim_d = gpd.GeoSeries(df['geometry'])
             geo_d = sim_d.to_json()
             geo_d = folium.GeoJson(data=geo_d,
                               style_function=lambda x: {'fillColor': 'red','fill_opacity':0.8,'color': 'red'})
             geo_d.add_to(m)
         
    m = m._repr_html_() #HTML representation of original m
    context = {

        'm': m,
        'd': d,

        }

    return render(request,'map4.html',context)


def serve_sites(df):

    file_name = 'optimized_sites.txt'
    response = HttpResponse(content_type='map5/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
    df.to_csv(response)
    return response
    
def map5(request):

    #Get insect type
    field_name = 'geometry2'
    obj = GEOM2.objects.first()
    field_object = GEOM2._meta.get_field(field_name)
    d2 = field_object.value_from_object(obj)
    

    from shapely import wkt

    d2 = wkt.loads(d2)

    gdf = gpd.GeoDataFrame(geometry=[d2], crs='epsg:4326')
    gdf['id'] = [1]

    e = test_form5(request)

    print(e)

    if e is not None:
        print('check4')
        e = int(e)

        try:
            inst = EXPORT.objects.create(nsite=e)
            inst_ini = EXPORT.objects.get(id=1)
        except: 
            if e is not None: 
                inst = EXPORT.objects.create(nsite=e)
                inst_ini = EXPORT.objects.get(id=1)
            else:
                inst = EXPORT.objects.create(nsite=e)
                inst_ini = EXPORT.objects.get(id=1) 
        if inst_ini == None: 
        
            inst_ini = EXPORT.objects.create(nsite=e)

        else:

            inst_ini.nsites = e
            inst_ini.save(update_fields=['nsite'])        
    else:
        e = -1
        inst = EXPORT.objects.create(nsite=5)
        inst_ini = EXPORT.objects.get(id=1) 


    if e > 0:
        from ortools.linear_solver import pywraplp
        gdf['dissolvefield'] = 1
        dgdf = gdf.buffer(0.0001)
        
        dgdf = gpd.GeoDataFrame(geometry=dgdf)
        dgdf['dissolvefield'] = 1
        dgdf = dgdf.dissolve(by='dissolvefield').dissolve()
        print(dgdf)
        
        e_gdf = dgdf.geometry.explode()
        e_gdf = gpd.GeoDataFrame(geometry=e_gdf, crs='epsg:4326')
        
        v = get_dist_haversine_polygon(e_gdf)
            #Optimize

        e_gdf['id_num'] = list(range(0,len(e_gdf)))
        op_list = [] 
        mdist_list = [] 
        site7_loc = [] 
        for row in e_gdf[['geometry','id_num']].iterrows():
            site = row
            print(list(row)[1])
            site = list(site)[1][0]
            site = gpd.GeoDataFrame(geometry=[site]) #Site[0]
            site = site.centroid
            loc = (float(site.x),float(site.y),)
            
            obj_func, info = optimize_for_site(loc,[v],e)
            op_list.append(info)

            mdist_list.append(obj_func)
            site7_loc.append([float(site.x),float(site.y),list(row)[0]])
        index_min = mdist_list.index(min(mdist_list))

        print('Selected Sites')
        print(op_list[index_min])
        print('Selected Site 7 Location')
        print(site7_loc[index_min])
        print('Minimum Haversine Dist Possible Bt Sites (km)')
        print(mdist_list[index_min])

        df_sites = op_list[index_min]

        df_sites = df_sites.append(pd.DataFrame([['x0', 0,site7_loc[index_min][1],\
                                       site7_loc[index_min][0],site7_loc[index_min][2][1],1.0]],columns=df_sites.columns))

        print(df_sites)

        list_of_ids = [int(x) for x in list(df_sites['id_num'])]

        e_gdf_f = e_gdf[e_gdf['id_num'].isin(list_of_ids)]

        if mdist_list[index_min] <= 10:

            z = 12
        elif mdist_list[index_min] <= 20:

            z = 10
        elif mdist_list[index_min] <= 20:
            z = 8
        else:
            z = 6

        lat = site7_loc[index_min][1]
        lon = site7_loc[index_min][0]

    else:
        d2 = -1
        z= 6
        lat = 48.63290858589535
        lon = -83.671875
        df_sites = pd.DataFrame()


    key = 'pk.eyJ1IjoiY2xhcmFyaXNrIiwiYSI6ImNrbjk5cGxoMjE1cHIydm4xNW55cmZ1cXgifQ.3CXp0GaWY1S7iMcPP8n9Iw'
    tile_input = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(key)

        
        
    print(z)
    m = folium.Map(location=[lat,lon],zoom_start=z,control_scale=True,tiles=tile_input,attr='Mapbox',API_key = key,prefer_canvas=True)
    
    if d2 != -1:
         print('Checkpoint1')
         
         r = e_gdf_f['geometry']
         print(r)

         sim_geo = gpd.GeoSeries(r) #.simplify(tolerance=1)
         geo_j = sim_geo.to_json()
         geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'green','fill_opacity':0.8,'color': 'green'})
         geo_j.add_to(m)
         print('check!')
         
    m = m._repr_html_() #HTML representation of original m
    context = {

        'm': m,

        }

    return render(request,'map5.html',context)


def map6(request):

    #Get insect type
    field_name = 'geometry2'
    obj = GEOM2.objects.first()
    field_object = GEOM2._meta.get_field(field_name)
    d2 = field_object.value_from_object(obj)
    

    from shapely import wkt

    d2 = wkt.loads(d2)

    gdf = gpd.GeoDataFrame(geometry=[d2], crs='epsg:4326')
    gdf['id'] = [1]

    #Get insect type
    field_name = 'nsite'
    obj = EXPORT.objects.first()
    field_object = EXPORT._meta.get_field(field_name)
    e = field_object.value_from_object(obj)

    if e is not None:
        e = int(e)
    else:
        e = -1

    if e > 0:
        from ortools.linear_solver import pywraplp
        gdf['dissolvefield'] = 1
        dgdf = gdf.buffer(0.0001)
        
        dgdf = gpd.GeoDataFrame(geometry=dgdf)
        dgdf['dissolvefield'] = 1
        dgdf = dgdf.dissolve(by='dissolvefield').dissolve()
        print(dgdf)
        
        e_gdf = dgdf.geometry.explode()
        e_gdf = gpd.GeoDataFrame(geometry=e_gdf, crs='epsg:4326')
        
        v = get_dist_haversine_polygon(e_gdf)
            #Optimize

        e_gdf['id_num'] = list(range(0,len(e_gdf)))
        op_list = [] 
        mdist_list = [] 
        site7_loc = [] 
        for row in e_gdf[['geometry','id_num']].iterrows():
            site = row
            print(list(row)[1])
            site = list(site)[1][0]
            site = gpd.GeoDataFrame(geometry=[site]) #Site[0]
            site = site.centroid
            loc = (float(site.x),float(site.y),)
            
            obj_func, info = optimize_for_site(loc,[v],e)
            op_list.append(info)

            mdist_list.append(obj_func)
            site7_loc.append([float(site.x),float(site.y),list(row)[0]])
        index_min = mdist_list.index(min(mdist_list))

        print('Selected Sites')
        print(op_list[index_min])
        print('Selected Site 7 Location')
        print(site7_loc[index_min])
        print('Minimum Haversine Dist Possible Bt Sites (km)')
        print(mdist_list[index_min])

        df_sites = op_list[index_min]

        df_sites = df_sites.append(pd.DataFrame([['x0', 0,site7_loc[index_min][1],\
                                       site7_loc[index_min][0],site7_loc[index_min][2][1],1.0]],columns=df_sites.columns))

        print(df_sites)

        list_of_ids = [int(x) for x in list(df_sites['id_num'])]

        e_gdf_f = e_gdf[e_gdf['id_num'].isin(list_of_ids)]

        if mdist_list[index_min] <= 10:

            z = 12
        elif mdist_list[index_min] <= 20:

            z = 10
        elif mdist_list[index_min] <= 20:
            z = 8
        else:
            z = 6

        lat = site7_loc[index_min][1]
        lon = site7_loc[index_min][0]

    else:
        d2 = -1
        z= 6
        lat = 48.63290858589535
        lon = -83.671875
        df_sites = pd.DataFrame()    


    if len(df_sites) > 0:

        file_name = 'optimized_sites.txt'
        response = HttpResponse(content_type='map6/force-download')
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
        df_sites.to_csv(response)
        return response
        

