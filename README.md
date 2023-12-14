# HousingAnalysis

Explicación de Estructura del Proyecto: 

  *Data: carpeta con csvs y datos de scrap. Utilizar archivos de Unificadas como base para todo análisis.
  *src: carpeta con jupyter notebooks que se utilizaron.

Cosas que se deben hacer:

  1- Implementar modelo predictivo. 
    *Para esto, se deberían utilizar los resumenes de barrios quincenales y algún algoritmo proveniente de statsmodels y que se especialice en hacer forecasting de datos con línea temporal (ej. ARMA).
    *OBSERVACIÓN: hay que ver como lograr la segmentación interna de los barrios para que los resultados sean más representativos (Dentro de un mismo barrio podría haber una zona lujosa y una marginal).
  
  2- Correcciones a los modelos estáticos.
    *Nos referimos con modelos estáticos a aquellos que solo utilizan datos de inmuebles "activos" en su quincena.
    *Se deben corregir y eficientizar los modelos para llegar a una precisión r2 > 0.80.
    *Fijarse en: parámetros utilizados en cada modelo, variables utilizadas...
    *RECOMENDACIÓN PERSONAL: los modelos deberían ser de tipo árbol de decisiones. Son los que consistentemente logran mayor precisión.