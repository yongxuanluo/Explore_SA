import pandas as pd
import numpy as np
from owslib.wms import WebMapService
import rasterio


#create wms connection
wms = WebMapService('https://services.sarig.sa.gov.au/raster/GCAS/wms?service=wms&version=1.1.1&REQUEST=GetCapabilities')
wms.contents

def raster_to_dataframe(layer_name, data_type):
    #check bounding coordinates
    bounding = wms[layer_name].boundingBoxWGS84
    
    #download raster from wms connection: 5000x5000 exceed memory threshold
    response = wms.getmap(
        layers=[layer_name],
        srs='EPSG:4326',
        bbox=(bounding[0:4]),
        size=(1000,1000),
        format='image/geotiff')
    
    #write raster file from http response: png,tiff,jpeg all render weirdly on qgis although the color looks more correct
    out = open('output_image/' + layer_name + '.geotiff', 'wb')
    out.write(response.read())
    out.close()
    
    #open raster
    raster = rasterio.open('output_image/' + layer_name + '.geotiff')
    
    #create dataframe that store all rgb values for each raster file obtain
    color = [data_type + '_red', data_type + '_green', data_type + '_blue']
    array = raster.read([1,2,3])
    flag = True
    for i in range(1,4):
        temp_coordinate = pd.DataFrame(
                            raster.read(i), 
                            index = [raster.xy(index,0)[1] for index in range(0,1000)],
                            columns = [raster.xy(0,index)[0] for index in range(0,1000)]
                        )
        temp_unstack = temp_coordinate.unstack()
        temp = temp_unstack.reset_index(name = color[i-1])
        temp.rename(columns={'level_0': 'y', 'level_1': 'x'}, inplace=True)
        if flag:
            data = temp
            flag = False
        else:
            data = data.merge(temp, on = ['x', 'y'])
    return(data)def raster_to_dataframe(layer_name, data_type, bounding_box):
    
    #download raster from wms connection: 5000x5000 exceed memory threshold
    response = wms.getmap(
        layers=[layer_name],
        srs='EPSG:4326',
        bbox=(bounding_box['left'], bounding_box['lower'], bounding_box['right'], bounding_box['upper']),
        size=(1000,1000),
        format='image/geotiff')
    
    #write raster file from http response: png,tiff,jpeg all render weirdly on qgis although the color looks more correct
    out = open('output_image/' + layer_name + '.geotiff', 'wb')
    out.write(response.read())
    out.close()
    
    #open raster
    raster = rasterio.open('output_image/' + layer_name + '.geotiff')
    
    #create dataframe that store all rgb values for each raster file obtain
    color = [data_type + '_red', data_type + '_green', data_type + '_blue']
    array = raster.read([1,2,3])
    flag = True
    for i in range(1,4):
        temp_coordinate = pd.DataFrame(
                            raster.read(i), 
                            index = [raster.xy(index,0)[1] for index in range(0,1000)],
                            columns = [raster.xy(0,index)[0] for index in range(0,1000)]
                        )
        temp_unstack = temp_coordinate.unstack()
        temp = temp_unstack.reset_index(name = color[i-1])
        temp.rename(columns={'level_0': 'y', 'level_1': 'x'}, inplace=True)
        if flag:
            data = temp
            flag = False
        else:
            data = data.merge(temp, on = ['x', 'y'])
    return(data)

#create a dataframe that contains bounding box coordinate for all three layers for each region
bbox_flag = True
for region_code in ['1a','1b','2a','2b','3a','3b','4a','4b','5','6','7','8a','8b','9a','9b','10']:
    for data_type_code in ['dem','mag','rad']:
        #get layer name
        t = [region_code + '_' + data_type_code in x for x in list(wms.contents)]
        layer_name = list(wms.contents)[[i for i, x in enumerate(t) if x][0]]
        #get bounding of the first layer to make sure three layers are sharing same coordinates for each pixel
        bounding = wms[layer_name].boundingBoxWGS84
        bbox_temp = pd.DataFrame([[region_code] + list(bounding)], columns = ['region','left','lower','right','upper'])
        if bbox_flag:
            bbox_all = bbox_temp 
            bbox_flag = False
        else:
            bbox_all = bbox_all.append(bbox_temp)
            
#create dataframe that has the largest extend of bounding box for each region
bbox_max = bbox_all.groupby(['region']).agg({'left':'min', 'right':'max', 'lower':'min', 'upper':'max'})
    
# loop through all data type for all regions and combine results together
all_result_flag = True
for region in ['1a','1b','2a','2b','3a','3b','4a','4b','5','6','7','8a','8b','9a','9b','10']:
    region_flag = True
    for data_type in ['dem','mag','rad']:
        #get layer name
        t = [region + '_' + data_type in x for x in list(wms.contents)]
        layer_name = list(wms.contents)[[i for i, x in enumerate(t) if x][0]]
        #get bounding of the first layer to make sure three layers are sharing same coordinates for each pixel
        bounding = bbox_max.loc[region,]
        temp = raster_to_dataframe(layer_name, data_type, bounding)
        if region_flag:
            region_result = temp
            region_flag = False
        else:
            region_result = region_result.merge(temp, on = ['x', 'y'], how = 'outer')
    if all_result_flag:
        all_result = region_result
        all_result_flag = False
    else:
        all_result = all_result.append(region_result)
