
def get_data():
    import pandas as pd
    import unidecode as udc
    import numpy as np
    
    # lectura de las bases de datos como data-frame con la dirección directa de las bases de datos
    cv_df = pd.read_csv('https://datosabiertos.bogota.gov.co/dataset/5e79c701-d02f-4220-a9ae-31c8def1cfab/resource/47c5207a-d597-4c9e-ad74-4fb980656bf8/download/osb_demografia-condicionesvida.csv', encoding='latin-1', delimiter=';', decimal=',')
    vi_df = pd.read_csv('https://datosabiertos.bogota.gov.co/dataset/a1e1ef90-10c0-436f-a290-d1f7c1cf2242/resource/ab4eeb6e-e7c1-4ec1-b3e5-eedc655bc8d7/download/osb_v-intrafamiliar.csv', encoding='latin-1', delimiter=';', decimal=',', thousands='.')
    sc_df = pd.read_csv('https://datosabiertos.bogota.gov.co/dataset/2b8464e3-3aca-4dcd-91a1-93dd06ddabbb/resource/f215cedd-46e0-44fe-ba4c-704afdc11a33/download/osb_saludmen-tsuicidiodesagregado.csv', encoding='latin-1', delimiter=';')
    
    # 'Cleaning' en los nombres y tipos de cada columna para un mejor acceso
    vi_df['Año'] = vi_df['Año'].str.extract(r'(\d{4})').astype(int)
    vi_df.columns = [udc.unidecode(i) for i in vi_df.columns.str.lower().str.replace('.', '', regex=False).str.replace(' ', '_', regex=False)]
    cv_df.columns = cv_df.columns.str.lower().str.replace(' ', '_')
    sc_df.columns = [udc.unidecode(i) for i in sc_df.columns.str.lower().str.replace(' ', '_', regex=False)]
    
    dfs = [cv_df, vi_df, sc_df]              # lista de data-frames
    
    # Homologación de categorías
    for i in dfs:
        if 'ano' in i.columns:
            i.rename(columns={'ano': 'year'}, inplace=True)
        if 'area' in i.columns:
            i.rename(columns={'area':'localidad'}, inplace=True)
            
    # Normalización de categorías        
    cv_df['localidad'] = cv_df['localidad'].map(udc.unidecode).str.lower().replace({'bogota d.c.': 'distrito'})
    sc_df['localidad'] = sc_df['localidad'].map(udc.unidecode).str.lower()
    vi_df['localidad'] = vi_df['localidad'].map(udc.unidecode).str.lower()
    
    cv_df['condiciones_de_vida'] = cv_df['condiciones_de_vida'].str.lower()
    vi_df['sexo'] = vi_df['sexo'].str.strip()
    
    # Completar valores faltantes en los numeros de casos con 0
    vi_df['no_casos'].fillna(0, inplace=True)                
    
    # Completar valores faltantes en la tasa por 100mil habitantes con la operacion (no_casos/poblacion)*100000
    vi_df['tasa_por_100000'].fillna((vi_df['no_casos']/vi_df['poblacion'])*100000, inplace=True)
    
    
    # Columna adicional para identificar el grupo etáreo de cada grupo edad
    
    # Diccionario con grupos de edad y respectivo grupo etáreo
    dic = {'Niño': sc_df['grupo_de_edad'].unique()[:2], 'Joven': sc_df['grupo_de_edad'].unique()[2:5], 'Adulto': sc_df['grupo_de_edad'].unique()[5:12], 'Adulto Mayor': sc_df['grupo_de_edad'].unique()[12:-1]}
    
    # Creación columna adicional vacía
    sc_df['grupo_etario'] = np.nan
    
    # Llenado columna vacía
    for i in dic:
        sc_df.loc[sc_df['grupo_de_edad'].isin(dic[i]),'grupo_etario'] = i
        
    # Columna adicional que lleve la población y la tasa de casos de suicidio por cada 100.000 habitantes
    
    # Obtener datos de población por cada año, localidad y sexo
    _1 = vi_df.groupby(['year', 'localidad', 'sexo'])[['year', 'localidad', 'sexo', 'poblacion']].sample(1) 
    
    # Unión de la columna de población
    sc_df = sc_df.merge(_1, on=['year', 'localidad', 'sexo'], how='inner') 
    
    # Creación de la columna de tasa por cada 100.000 habitantes
    sc_df['tasa_por_100000'] = (sc_df['casos']/sc_df['poblacion'])*100000 
    
    # Filtrado para llenar solo la información diferenciada por grupo de edad
    sc_df.loc[sc_df['grupo_de_edad'] != 'Todos los grupos', ['tasa_por_100000', 'poblacion']] = np.nan
    
    sc_df.to_csv('suicidios_mod.csv', index=False)
    vi_df.to_csv('violencia_mod.csv', index=False)
    cv_df.to_csv('condicion_mod.csv', index=False)


