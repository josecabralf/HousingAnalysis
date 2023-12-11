import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from math import radians, sin, cos, sqrt, atan2
from config import map_barrios, map_comisarias, map_ctros_salud, map_transporte_urb


class DataFilter:
  def filterAttributes(self, df: pd.DataFrame):
    data = df.copy()
    data = data.loc[data["cantBanos"].notna() & data["cantDormitorios"].notna()]
    data = data.loc[(data["terrenoEdificado"]>data["terrenoEdificado"].quantile(0.02)) &
                    (data["terrenoEdificado"]<data["terrenoEdificado"].quantile(0.98))]
    data = data.loc[(data["precioUSD"]>data["precioUSD"].quantile(0.02)) &
                    (data["precioUSD"]<data["precioUSD"].quantile(0.98))]
    return data

  def filtMap(self, df):
    data = df.copy()
    barrios = gpd.read_file(map_barrios)
    geometry = [Point(xy) for xy in zip(data['coordY'], data['coordX'])]
    data_geo = gpd.GeoDataFrame(data, geometry=geometry, crs=barrios.crs)

    data = gpd.sjoin(data_geo, barrios, how="inner", op='within')
    data = data.loc[:, "tipoPropiedad":"geometry"]
    return data

  def formatDF(self, df):
    data = self.filterAttributes(df)
    data.drop_duplicates(subset=["coordX", "coordY"], keep="first", inplace=True)
    data = self.filtMap(data)
    data = self.formatDate(data)
    data.drop(columns=["fechaUltimaActualizacion", "geometry", "URL"], inplace=True)
    data = self.discretizarDatos(data)
    return data

  def discretizarDatos(self, df):
    data = df.copy()
    data = self.discretizarTiposPropiedad(data)
    data = self.discretizarTipoVendedor(data)
    data = self.discretizarBarrios(data)
    return data
    
  def discretizarTiposPropiedad(self, df):
    data = df.copy()
    tiposPropiedad = {"CASA": 1,
                      "DEPARTAMENTO": 2,
                      "TERRENO": 3}
    data.loc[:, "tipoPropiedad"] = data["tipoPropiedad"].map(tiposPropiedad)
    return data

  def definirTipoVendedor(self, x):
    if x=="INMOBILIARIA": return 0
    if x=="PARTICULAR": return 1
    return 2

  def discretizarTipoVendedor(self, df):
    data = df.copy()
    data.loc[:, "vendedor"] = data.loc[:, "vendedor"].apply(lambda x: self.definirTipoVendedor(x))
    return data

  def discretizarBarrios(self, df):
    data = df.copy()
    barrios = pd.read_csv("./utils/barrios.csv")
    data.loc[:, "barrioID"] = -1
    for barrio in barrios["barrio"]: 
      data.loc[data["barrio"] == barrio, "barrioID"] = barrios.loc[barrios["barrio"] == barrio].index[0]
    for b in data.loc[data["barrioID"] == -1, "barrio"].unique():
      data.loc[data["barrio"] == b, "barrioID"] = data["barrioID"].max()+1
    return data
  
  def formatDate(self, df):
    data = df.copy()
    data['fechaUltimaActualizacion'] = pd.to_datetime(data['fechaUltimaActualizacion'])
    data["ano"] = data["fechaUltimaActualizacion"].dt.year
    data["mes"] = data["fechaUltimaActualizacion"].dt.month
    data["dia"] = data["fechaUltimaActualizacion"].dt.day
    return data
    
    
class DistanceCalculator:
  def __init__(self) -> None:
    self.comisarias = pd.read_csv(map_comisarias)
    self.centros_salud = gpd.read_file(map_ctros_salud)
    self.transporte = pd.read_csv(map_transporte_urb)

    self.comisarias = gpd.GeoDataFrame(self.comisarias, geometry=gpd.points_from_xy(self.comisarias.Longitud, self.comisarias.Latitud))
    self.transporte = gpd.GeoDataFrame(self.transporte, geometry=gpd.points_from_xy(self.transporte.Longitud, self.transporte.Latitud))
     
  def calcular_distancia_por_coords(self, coord1, coord2):
      radio_tierra = 6371.0
      latitud1, longitud1 = radians(coord1[0]), radians(coord1[1])
      latitud2, longitud2 = radians(coord2[0]), radians(coord2[1])

      dlat = latitud2 - latitud1
      dlon = longitud2 - longitud1

      a = sin(dlat / 2)**2 + cos(latitud1) * cos(latitud2) * sin(dlon / 2)**2
      c = 2 * atan2(sqrt(a), sqrt(1 - a))
      distancia = radio_tierra * c

      return distancia
    
  def calcular_distancia_minima(self, coord, coords):
      distancias = []
      for c in coords:
          distancias.append(self.calcular_distancia_por_coords(coord, c))
      return min(distancias)

  def calcular_distancia_minima_comisarias(self, coord, comisarias):
      return self.calcular_distancia_minima(coord, comisarias[["Latitud", "Longitud"]].values)

  def calcular_distancia_minima_tu(self, coord, transporte):
      return self.calcular_distancia_minima(coord, transporte[["Latitud", "Latitud"]].values)

  def calcular_distancia_minima_cs(self, coord, centros_salud):
      return self.calcular_distancia_minima(coord, centros_salud[["Latitud", "Longitud"]].values)

  def calcular_distancia_centro(self, coord):
      return self.calcular_distancia_por_coords(coord, (-31.4201, -64.1888))

  def calcular_distancias(self, df):
    data = df.copy()
    print("Calculando distancias...")
    data = data.loc[data["coordX"].notna()]
    
    print("Calculando comisariaCercana...")
    data["comisariaCercana"] = data[["coordX", "coordY"]].apply(
      lambda x: self.calcular_distancia_minima_comisarias(x, self.comisarias), axis=1)
    
    print("Calculando transporteCercano...")
    data["transporteCercano"] = data[["coordX", "coordY"]].apply(
      lambda x: self.calcular_distancia_minima_tu(x, self.transporte), axis=1)
    
    print("Calculando saludCercana...")
    data["saludCercana"] = data[["coordX", "coordY"]].apply(
      lambda x: self.calcular_distancia_minima_cs(x, self.centros_salud), axis=1)
    return data