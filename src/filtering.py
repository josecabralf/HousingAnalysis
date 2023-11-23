import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from config import map_barrios

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

def valorar_atributo(at, mean, std):
  if at<mean-2*std: return 2
  if at<mean-std: return 1
  if at<mean: return 0
  if at<mean+2*std: return -1
  if at<mean+3*std: return -2
  return -3


def addValues(df):
  data = df.copy()
  data["valComisaria"] = data["comisariaCercana"].apply(lambda x: valorar_atributo(x, data["comisariaCercana"].mean(), data["comisariaCercana"].std()))
  data["valTransporte"] = data["transporteCercano"].apply(lambda x: valorar_atributo(x, data["transporteCercano"].mean(), data["transporteCercano"].std()))
  data["valSalud"] = data["saludCercana"].apply(lambda x: valorar_atributo(x, data["saludCercana"].mean(), data["saludCercana"].std()))

  data.loc[:, "valoracionServicios"] = data["valComisaria"] + data["valTransporte"] + data["valSalud"]

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
  data = addValues(data)
  data = filtMap(data)
  return data


def discretizarDatos(df):
  data = df.copy()
  data = discretizarTiposPropiedad(data)
  data = discretizarTipoVendedor(data)
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