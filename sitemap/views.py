from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.utils.encoding import smart_str
import folium
import geopandas as gpd
import pandas as pd
from shapely import wkt
import uuid
from ortools.linear_solver import pywraplp
import json
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
from .models import AGEOM
from .models import ASM_Geom
from .models import EXPORT
from .models import FORCE
from .models import PAGE
from .models import OPTION
from .models import CHOICE
import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geospatialproject.settings")

# Create your views here.


def read_data(fp):

    return gpd.read_file(fp)

def get_dist_haversine_polygon(data):
    centroids = data.centroid[0]
    
    site_options = {} 
    for i in range(len(data)):
        x1, y1 = centroids[i].x, centroids[i].y

        df = pd.DataFrame() 
        dist_list, lon_list, lat_list, id_list = [], [], [], []

        for j in range(len(data)):
            x2, y2 = centroids[j].x, centroids[j].y
            if (x1,y1) != (x2,y2): 

                lon1, lat1 = math.radians(x1), math.radians(y1)
                lon2, lat2 = math.radians(x2), math.radians(y2) 

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
                id_list.append(j)

        df['polyid'] = id_list 
        df['dist'] = dist_list
        df['lon'] = lon_list
        df['lat'] = lat_list
        site_options[(x1,y1)] = df

    return site_options


def optimize_for_site(site,dictionary_list,n):
    """_summary_

    Args:
        site: Takes in each site
        dictionary_list: _description_
        n: _description_

    Returns:
        _description_
    """

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
        nsite_total = n-1
        solver.Add(sum(list_of_con) == nsite_total)

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

def build_page_context(pageNum):
    """Build the context with information about what the current step contains.
    This information is used by the Front End to know what to display

    Args:
        pageNum: Step number

    Returns:
        Context populated with the information required by the Front End to build a page
    """
    page = PAGE.objects.get(pk=pageNum)
    options = page.options.all()
    numOptions = len(options)
    context = {
        'pageNum': pageNum,
        'stepTitle': page.title,
        'numOptions': numOptions,
        'options': []
        }


    for i in range(numOptions):
        option = options[i]
        choices = option.choices.all()
        numChoices = len(choices)
        optionType = option.types

        new_dict = {
            'description': option.description,
            'type': optionType,
            'numChoices': numChoices,
            'minimum': json.dumps(option.minimum),
            'maximum': json.dumps(option.maximum),
            'step': json.dumps(option.step),
            'choices': []
        }

        if optionType == "DDN":
            new_dict["default"] = choices[0].choice
        elif optionType == "SLD":
            new_dict["default"] = option.minimum

        for j in range(numChoices):
            choice = choices[j]
            new_dict['choices'].append(choice.choice)

        context["options"].append(new_dict)
    
    return context

def update_context_with_defaults(pageNum, context, post):
    """Update all the options default values to be the previously selected values
    This ensures that the options on the Front-End don't change when the map is updated

    Args:
        pageNum: Step number
        context: Context to send to the Front End, already populated
        post: POST request body, which includes what the user has selected

    Returns:
        Context with the updated defaults
    """
    page = PAGE.objects.get(pk=pageNum)
    options = page.options.all()
    numOptions = len(options)
    for i in range(numOptions):
        option = options[i]
        context["options"][i]["default"] = post[option.description]

    return context

def get_empty_map():
    """Get an empty map to populate (or not) later

    Returns:
        An empty map
    """
    key = 'pk.eyJ1IjoiY2xhcmFyaXNrIiwiYSI6ImNrbjk5cGxoMjE1cHIydm4xNW55cmZ1cXgifQ.3CXp0GaWY1S7iMcPP8n9Iw'
    tile_input = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(key)

    return folium.Map(location=[48.63290858589535,-83.671875],zoom_start=5,control_scale=True,tiles=tile_input,attr='Mapbox',API_key = key,prefer_canvas=True)

def get_choiceCode(option, selection):
    """Helper function to get the choice code for a particular option.
    The choice code is what will be used to build the path to the geojson file.
    For example, when the user selects "Jack Pine Budworm", the choice Code could be "jpb"

    Args:
        option: Which option to get the code for
        selection: What the user has selected for that option (the choice that was selected)

    Returns:
        Code for the selected choice
    """

    try:
        choice = option.choices.get(choice=selection)
    except:
        return ""
    return choice.choiceCode

def save_cached_map(uuid):
    """Write or Overwrite the user's Saved map with the user's Cached map
    Is used between steps to allow to come back to the map as it was at the beginning of the step

    Args:
        uuid: User's ID
    """
    try:
        geometry = GEOM.objects.get(uuid = uuid)
    except:
        return
    geometry.geometry = geometry.cachedGeometry
    geometry.save()

def get_saved_map(uuid):
    """Helper function to get the user's saved map.
    Assumes the user has a saved map (this is not the cached map)
    Converts the data saved to the database to an actual map

    Args:
        uuid: user's ID

    Returns:
        HTML representation of the user's saved map. Can be added directly to the Context and returned to the Front-End
    """
    geoMap = get_empty_map()

    try:
        geometry = GEOM.objects.get(uuid = uuid)
    except:
        return geoMap._repr_html_()

    lastMap = wkt.loads(geometry.geometry)

    gdf = gpd.GeoDataFrame(geometry=[lastMap], crs='epsg:4326').to_json()

    geo_j = folium.GeoJson(data=gdf,
                style_function=lambda x: {'fillColor': 'green','color': 'green'})
    geo_j.add_to(geoMap)
    return geoMap._repr_html_()

def clear_map(uuid):
    """Deletes the user's saved map, if it exists.

    Args:
        uuid: User's ID
    """
    try:
        geometry = GEOM.objects.get(uuid = uuid)
    except:
        return
    geometry.delete()

def upload_sites(uuid):
    """Get saved map for user, and prepare it for sending the file to the user.

    Args:
        uuid: User's ID

    Returns:
        Response including the data in a csv format ready to return to the user.
    """
    file_name = 'optimized_sites.txt'
    response = HttpResponse(content_type='')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)

    geometry = GEOM.objects.get(uuid = uuid)

    lastMap = wkt.loads(geometry.geometry)

    gdf = gpd.GeoDataFrame(geometry=[lastMap], crs='epsg:4326').explode()['geometry'][0]

    gdf = pd.DataFrame(gdf)

    gdf.to_csv(response)
    return response


def update_map(geoMap, data, operation, uuid):
    """Update map with new data.
    If no map is currently saved for the user, make a map with data

    Args:
        geoMap: Current map
        data: New data to add to the map
        operation: What to do with data. Default is "intersection"
        uuid: User's ID

    Returns:
        Updated map, Updated data after operation is applied
    """
    try:
        geometry = GEOM.objects.get(uuid = uuid)
    except:
        for _, row in data.iterrows():

            sim_geo = gpd.GeoSeries(row['geometry'])
            geo_j = sim_geo.to_json()
            geo_j = folium.GeoJson(data=geo_j,
                        style_function=lambda x: {'fillColor': 'green','color': 'green'})
            geo_j.add_to(geoMap)
        return geoMap, data

    lastMap = wkt.loads(geometry.geometry)

    gdf = gpd.GeoDataFrame(geometry=[lastMap], crs='epsg:4326')

    if operation == None:
        geo_j = data.to_json()
        geo_j = folium.GeoJson(data=geo_j,
                    style_function=lambda x: {'fillColor': 'green','color': 'green'})
        geo_j.add_to(geoMap)
        return geoMap, data
    elif operation == "intersection":
        
        intersect = data.intersection(gdf['geometry'])

        geo_j = intersect.to_json()
        geo_j = folium.GeoJson(data=geo_j,
                    style_function=lambda x: {'fillColor': 'green','color': 'green'})
        geo_j.add_to(geoMap)

        return geoMap, intersect
    elif operation == "clip":
        
        clip = gdf.clip(data['geometry'])

        geo_j = clip.to_json()
        geo_j = folium.GeoJson(data=geo_j,
                    style_function=lambda x: {'fillColor': 'green','color': 'green'})
        geo_j.add_to(geoMap)

        return geoMap, clip
    elif operation == "difference":

        difference = gdf.difference(data.dissolve()['geometry'])

        geo_j = difference.to_json()
        geo_j = folium.GeoJson(data=geo_j,
                    style_function=lambda x: {'fillColor': 'green','color': 'green'})
        geo_j.add_to(geoMap)

        return geoMap, difference

def write_or_overwrite_saved_cached_geometry(data, uuid):
    """Saves map data to the user's cached geometry object.
    Creates a geometry object for the user if it doesn't exist, 
    Otherwise it overwrites the current cached geometry.

    Args:
        data: geometry data to save. Only the first row is saved (row 0)
        uuid: User's ID
    """
    try:
        geometry = GEOM.objects.get(uuid = uuid)
    except:
        GEOM.objects.create(cachedGeometry=str(data[0]), uuid=uuid)
        return
    geometry.cachedGeometry = data[0]
    geometry.save()
        
def select_attribute(data, attributeName, selection, operation):
    """Helper function to select attributes within the data. Example YEAR attribute >= 2010

    Args:
        data: Data to parse
        attributeName: Key of the attribute. Example: YEAR, DATE
        selection: What argument to use in the selection. Example: 2010 in YEAR >= 2010
        operation: Which operation to use. Based off CHOICE.OPERATION model. Example "EQU" => ==

    Returns:
        The rows of data that satisfy the constraints
    """
    if operation == "EQU":
        return data[data[attributeName] == selection]
    elif operation == "GOE":
        return data[data[attributeName] >= selection]
    elif operation == "SOE":
        return data[data[attributeName] <= selection]
    elif operation == "STG":
        return data[data[attributeName] > selection]
    elif operation == "STS":
        return data[data[attributeName] < selection]

def get_map(pageNum, post, uuid):
    """Get a map populated with the geographical data at the current step.

    Args:
        pageNum: Step number
        post: POST request body. Usually accessed through request.POST
        uuid: current user's ID

    Returns:
        HTML representation of the map. Can be added directly to the Context and returned to the Front-End
    """
    page = PAGE.objects.get(pk=pageNum)
    options = page.options.all()
    numOptions = len(options)

    data = None

    geoMap = get_empty_map()
    
    
    if page.operationType == "attributeSelection":
        
        firstOption = options[0]

        geoFile = firstOption.geoFile

        if option.types == "SLD":
            geoFile += selection
        else:
            geoFile += get_choiceCode(option, post[firstOption.description])

        geoFile += ".geojson"

        data = read_data(geoFile)

        for i in range(1, numOptions):
            option = options[i]

            selection = post[option.description]
            if option.types == "SLD":
                selection = float(selection)

            data = select_attribute(data, option.attribute, selection, option.operation)
            
    elif page.operationType == "fileSelection":
        firstOption = options[0]

        geoFile = firstOption.geoFile + get_choiceCode(firstOption, post[firstOption.description])

        for i in range(1, numOptions):
            option = options[i]
            selection = post[option.description]

            if option.types == "SLD":
                geoFile += option.geoFile + selection
            else:
                geoFile += option.geoFile + get_choiceCode(option, selection)

        geoFile += ".geojson"
        
        try:
            data = read_data(geoFile)
        except:
            return geoMap._repr_html_()

    elif page.operationType == "areaComputation":
        geometry = GEOM.objects.get(uuid = uuid)

        lastMap = wkt.loads(geometry.geometry)

        data = gpd.GeoDataFrame(geometry=[lastMap], crs='epsg:4326')

        data = data.to_crs('esri:102001')

        data = data.explode(index_parts = False)

        data['area'] = data['geometry'].area / 10**6

        for i in range(numOptions):
            option = options[i]

            selection = post[option.description]

            if option.types == "SLD":
                selection = float(selection)

            data = select_attribute(data, "area", selection, option.operation)
            data = gpd.GeoDataFrame(geometry=data['geometry'], crs='esri:102001')
        data = data.dissolve()
        data = data.to_crs('epsg:4326')

    elif page.operationType == "buffer":
        for i in range(numOptions):
            option = options[i]
            geoFile = option.geoFile + ".geojson"

            readData = read_data(geoFile).to_crs('esri:102001')

            selection = float(post[option.description])

            buffer = readData.geometry.buffer(selection).unary_union

            buffer_df = gpd.GeoDataFrame(geometry=[buffer], crs='esri:102001')

            if data == None:
                data = buffer_df
            else:
                data = data.union(buffer_df)
            data = data.dissolve()
            data = data.to_crs('epsg:4326')
    elif page.operationType == "selectSites":
        geometry = GEOM.objects.get(uuid = uuid)

        option = options[0]

        selection = int(post[option.description])

        lastMap = wkt.loads(geometry.geometry)

        data = gpd.GeoDataFrame(geometry=[lastMap], crs='epsg:4326')
        
        # data = data.buffer(0.0001) # This solves Ring intersection error (or something). Bug
        
        # data = gpd.GeoDataFrame(geometry=data)
        # data['dissolvefield'] = 1  #All polygons are separate, this dissolves into 1 polygon. Creating a new column is to dissolve according to that column
        # data = data.dissolve(by='dissolvefield').dissolve()
        
        data = data.geometry.explode() # Now the linear thing bug is fixed, exploding into separate polygons again
        data = gpd.GeoDataFrame(geometry=data, crs='epsg:4326')
        
        v = get_dist_haversine_polygon(data) #helper?
            #Optimize

        op_list = [] 
        mdist_list = [] 
        site_of_interest = [] 

        for i, row in data[['geometry']].iterrows():
            index = i[1]
            site = gpd.GeoDataFrame(geometry=row)
            siteCentroid = site.centroid
            location = (float(siteCentroid.x), float(siteCentroid.y))

            objective_function, information = optimize_for_site(location, [v], selection)
            op_list.append(information)
            mdist_list.append(objective_function)
            site_of_interest.append([location[0], location[1], index])

        index_min = mdist_list.index(min(mdist_list))
        missing_site_info = site_of_interest[index_min]
        optimal_sites = op_list[index_min]
        missing_site = pd.DataFrame([['x0', 0, missing_site_info[1], missing_site_info[0], \
            missing_site_info[2],1.0]],columns=op_list[index_min].columns)
        

        optimal_sites = pd.concat([optimal_sites, missing_site], ignore_index=True)

        list_of_ids = [int(x) for x in list(optimal_sites['id_num'])]

        data = data.iloc[list_of_ids]


    if data.empty:
        return geoMap._repr_html_()

    updatedMap, data = update_map(geoMap, data, page.betweenStepOperation, uuid)
    
    try:
        save_data = data.dissolve()['geometry']

    except:
        save_data = data

    write_or_overwrite_saved_cached_geometry(save_data, uuid)

    return updatedMap._repr_html_()
      
def get_pages(request):
    """Does all the heavy lifting: Sends the map and building instructions to the Front-End

    Args:
        request: Django Request.

    Returns:
        Information required by Django to send the instructions to the Front-End
    """
    if not 'uuid' in request.session:
        request.session['uuid'] = str(uuid.uuid4())
        
    uuid = request.session['uuid']

    pageNum = request.POST.get('pageNum')
    nextStep = request.POST.get('submit') == "nextStep"
    if pageNum == None:
        pageNum = 1
    if nextStep:
        pageNum = int(pageNum) + 1
        
    try:
        PAGE.objects.get(pk=pageNum)
    except:
        save_cached_map(uuid)
        return upload_sites(uuid)

    context = build_page_context(pageNum)


    context["map"] = get_empty_map()._repr_html_()
    if request.method == "POST":    
        if nextStep:
            save_cached_map(uuid)
            context["map"] = get_saved_map(uuid)
        else:
            context = update_context_with_defaults(pageNum, context, request.POST)
            context["map"] = get_map(pageNum, request.POST, uuid)
    else:
        if pageNum == 1:
            clear_map(uuid)
        
    
    return render(request,'index.html',context)

