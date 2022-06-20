import os
import pandas as pd
import geopandas as gpd

from gefxml_reader import Cpt

from shapely.geometry import Point

path = 'd:/GEF_los/'

fileList = [f'{path}{f}' for f in os.listdir(path) if f.lower().endswith('gef')]

projectids = []
projectnames = []
companies = []
tests = []
geometries = []
df = pd.DataFrame()

for f in fileList:
    cpt = Cpt()
    cpt.load_gef(f)
    projectids.append(cpt.projectid)
    projectnames.append(cpt.projectname)
    tests.append(cpt.testid)
    companies.append(cpt.companyid)
    geometries.append(Point(cpt.easting, cpt.northing))

df["projectid"] = projectids
df["projectname"] = projectnames
df["test"] = tests
df["company"] = companies
gdf = gpd.GeoDataFrame(df, geometry=geometries).set_crs("EPSG:28992")
gdf.to_file(f'./output/GEF_los.gpkg', driver='GPKG')