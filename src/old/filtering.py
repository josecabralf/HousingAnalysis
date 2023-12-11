import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from math import radians, sin, cos, sqrt, atan2
from config import map_barrios, map_comisarias, map_ctros_salud, map_transporte_urb

def filterAttributes(df: pd.DataFrame):
  data = df.copy()
  data = data.loc[data["cantBanos"].notna() & data["cantDormitorios"].notna() & data["cantCochera"].notna()]
  data = data.loc[data["coordX"].notna()]
  data = data.loc[(data["terrenoEdificado"]>data["terrenoEdificado"].quantile(0.02)) &
                  (data["terrenoEdificado"]<data["terrenoEdificado"].quantile(0.98))]
  data = data.loc[(data["precioUSD"]>data["precioUSD"].quantile(0.02)) &
                  (data["precioUSD"]<data["precioUSD"].quantile(0.98))]
  data.loc[:, "pm2"] = data["precioUSD"]/data["terrenoEdificado"]
  data = data.loc[(data["pm2"] < data["pm2"].quantile(0.99)) & (data["pm2"] > data["pm2"].quantile(0.01))]
  return data

def addNormalized(df):
  data = df.copy()
  data["terrenoEdificadoNormalized"] = (
    data["terrenoEdificado"] - data["terrenoEdificado"].mean())/data["terrenoEdificado"].std()
  data["precioUSDNormalized"] = (data["precioUSD"] - data["precioUSD"].mean())/data["precioUSD"].std()
  data.loc[:, "pm2Normalized"] = (data["pm2"] - data["pm2"].mean())/data["pm2"].std()
  
  data.loc[:, "distanciaCentroNormalized"] = (
    data["distanciaCentro"] - data["distanciaCentro"].mean())/data["distanciaCentro"].std()
  data.loc[:, "distanciaComisariaNormalized"] = (
    data["comisariaCercana"] - data["comisariaCercana"].mean())/data["comisariaCercana"].std()
  data.loc[:, "distanciaTransporteNormalized"] = (
    data["transporteCercano"] - data["transporteCercano"].mean())/data["transporteCercano"].std()
  data.loc[:, "distanciaSaludNormalized"] = (
    data["saludCercana"] - data["saludCercana"].mean())/data["saludCercana"].std()
  
  return data

def filtMap(df):
  data = df.copy()
  barrios = gpd.read_file(map_barrios)
  geometry = [Point(xy) for xy in zip(data['coordY'], data['coordX'])]
  data_geo = gpd.GeoDataFrame(data, geometry=geometry, crs=barrios.crs)

  data = gpd.sjoin(data_geo, barrios, how="inner", op='within')
  data = data.loc[:, "tipoPropiedad":"geometry"]
  return data

def formatDF(df):
  data = filterAttributes(df)
  data.drop_duplicates(subset=["coordX", "coordY"], keep="first", inplace=True)
  #data = addNormalized(data)
  data = calcularDistancias(data)
  data = filtMap(data)
  return data


def discretizarDatos(df):
  data = df.copy()
  data = discretizarTiposPropiedad(data)
  data = discretizarTipoVendedor(data)
  data = discretizarBarrios(data)
  return data
  
def discretizarTiposPropiedad(df):
  data = df.copy()
  tiposPropiedad = {"CASA": 1,
                    "DEPARTAMENTO": 2,
                    "TERRENO": 3}
  data.loc[:, "tipoPropiedad"] = data["tipoPropiedad"].map(tiposPropiedad)
  return data

def definirTipoVendedor(x):
  if x=="INMOBILIARIA": return 0
  if x=="PARTICULAR": return 1
  return 2

def discretizarTipoVendedor(df):
  data = df.copy()
  data.loc[:, "vendedor"] = data.loc[:, "vendedor"].apply(lambda x: definirTipoVendedor(x))
  return data

def discretizarBarrios(df):
  data = df.copy()
  barrios = pd.read_csv("./utils/barrios.csv")
  data.loc[:, "barrioID"] = -1
  for barrio in barrios["barrio"]: 
    data.loc[data["barrio"] == barrio, "barrioID"] = barrios.loc[barrios["barrio"] == barrio].index[0]
  for b in data.loc[data["barrioID"] == -1, "barrio"].unique():
    data.loc[data["barrio"] == b, "barrioID"] = data["barrioID"].max()+1
  return data

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

def calcular_distancia_minima_comisarias(coord, comisarias):
    return calcular_distancia_minima(coord, comisarias[["Latitud", "Longitud"]].values)

def calcular_distancia_minima_tu(coord, transporte):
    return calcular_distancia_minima(coord, transporte[["Latitud", "Latitud"]].values)

def calcular_distancia_minima_cs(coord, centros_salud):
    return calcular_distancia_minima(coord, centros_salud[["Latitud", "Longitud"]].values)

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
    lambda x: calcular_distancia_minima_comisarias(x, comisarias), axis=1)
  data["transporteCercano"] = data[["coordX", "coordY"]].apply(
    lambda x: calcular_distancia_minima_tu(x, transporte), axis=1)
  data["saludCercana"] = data[["coordX", "coordY"]].apply(
    lambda x: calcular_distancia_minima_cs(x, centros_salud), axis=1)
  data["distanciaCentro"] = data[["coordX", "coordY"]].apply(calcular_distancia_centro, axis=1)
  return data