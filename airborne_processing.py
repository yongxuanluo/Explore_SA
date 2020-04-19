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
    return(data)
    
# loop through all data type for all regions and combine results together
all_result_flag = True
for region in ['1a','1b','2a','2b','3a','3b','4a','4b','5','6','7','8a','8b','9a','9b','10']:
    region_flag = True
    for data_type in ['dem','mag','rad']:
        t = [region + '_' + data_type in x for x in list(wms.contents)]
        layer_name = list(wms.contents)[[i for i, x in enumerate(t) if x][0]]
        temp = raster_to_dataframe(layer_name, data_type)
        if region_flag:
            region_result = temp
            region_flag = False
        else:
            region_result = region_result.merge(temp, on = ['x', 'y'])
    if all_result_flag:
        all_result = region_result
        all_result_flag = False
    else:
        all_result = all_result.append(region_result)
