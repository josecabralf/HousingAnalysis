import geopandas as gpd
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from config import map_comisarias, map_ctros_salud, map_transporte_urb

def calcular_distancia(coord1, coord2):
    radio_tierra = 6371.0
    latitud1, longitud1 = radians(coord1[0]), radians(coord1[1])
    latitud2, longitud2 = radians(coord2[0]), radians(coord2[1])

    dlat = latitud2 - latitud1
    dlon = longitud2 - longitud1

    a = sin(dlat / 2)**2 + cos(latitud1) * cos(latitud2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distancia = radio_tierra * c

    return distancia
  
def calcular_distancia_minima(coord, coords):
    distancias = []
    for c in coords:
        distancias.append(calcular_distancia(coord, c))
    return min(distancias)

def calcular_distancia_minima_servicio(coord, servicio):
    return calcular_distancia_minima(coord, servicio[["Latitud", "Longitud"]].values)

def calcular_distancia_centro(coord):
    return calcular_distancia(coord, (-31.4201, -64.1888))

def calcularDistancias(df):
  data = df.copy()
  comisarias = pd.read_csv(map_comisarias)
  centros_salud = gpd.read_file(map_ctros_salud)
  transporte = pd.read_csv(map_transporte_urb)

  comisarias = gpd.GeoDataFrame(comisarias, geometry=gpd.points_from_xy(comisarias.Longitud, comisarias.Latitud))
  transporte = gpd.GeoDataFrame(transporte, geometry=gpd.points_from_xy(transporte.Longitud, transporte.Latitud))
  
  data["comisariaCercana"] = data[["coordX", "coordY"]].apply(
    lambda x: calcular_distancia_minima_servicio(x, comisarias), axis=1)
  data["transporteCercano"] = data[["coordX", "coordY"]].apply(
    lambda x: calcular_distancia_minima_servicio(x, transporte), axis=1)
  data["saludCercana"] = data[["coordX", "coordY"]].apply(
    lambda x: calcular_distancia_minima_servicio(x, centros_salud), axis=1)
  data["distanciaCentro"] = data[["coordX", "coordY"]].apply(calcular_distancia_centro, axis=1)
  return data