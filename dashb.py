import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
import numpy as np
import geojson
from datos import get_data

get_data()


def main():
    @st.cache(persist=True)
    def load_data():
        df_1 = pd.read_csv("suicidios_mod.csv")
        df_2 = pd.read_csv("violencia_mod.csv")
        df_3 = pd.read_csv("condicion_mod.csv")
        return df_1, df_2, df_3
      
    def get_table_download_link(df):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
        href = f'<a href="data:file/csv;base64,{b64}" download="datos.csv">Descargar archivo csv</a>'
        return href
        # return b64
    
    def get_img_download_link(fig):
        buffer = io.StringIO()
        fig.write_html(buffer, include_plotlyjs='cdn')
        html_bytes = buffer.getvalue().encode()
        
        return html_bytes
       
       
    sc_df, vi_df, cv_df = load_data()
    
    st.sidebar.markdown("<h2 style='text-align: left; color: black;'>Elija el tipo de información a visualizar</h2>", unsafe_allow_html=True)
    
    datos = st.sidebar.selectbox("", ("Todo","Suicidios", "Violencia", "Condiciones de Vida"))
    
    
       
    st.markdown("<h1 style='text-align: center; color: black;'>Análisis de la salud mental en la ciudad de Bogotá</h1>", unsafe_allow_html=True)
       
    c1, c2, c3 = st.columns((1,1,1))
    
    c1.markdown("<h6 style='text-align: center; color:black;'>Localidades con mas casos de Suicidios</h6>", unsafe_allow_html=True)
    df = sc_df.query("localidad != 'distrito' & grupo_de_edad == 'Todos los grupos'").groupby("localidad", as_index=False)["casos"].sum().sort_values("casos", ascending=False).head()
    # df = sc_df.query("grupo_de_edad == 'Todos los grupos' & localidad != 'distrito'").groupby("localidad", as_index=False)['tasa_por_100000'].sum().sort_values('tasa_por_100000', ascending=False).head()
    x = ['**{}**: {}'.format(df.iloc[i, 0].title(), df.iloc[i, 1]) for i in range(df.shape[0])]
    c1.info('\n\n'.join(x))
    
    c2.markdown("<h6 style='text-align: center; color:black;'>Localidades con mas casos de Violencia</h6>", unsafe_allow_html=True)
    df = vi_df.query("localidad != 'distrito' & year >= 2015 & tipo_de_violencia != 'intrafamiliar' & sexo == 'Total general'").groupby("localidad", as_index=False)["no_casos"].sum().sort_values("no_casos", ascending=False).head()
    # df = vi_df.query("localidad != 'distrito' & tipo_de_violencia != 'intrafamiliar' & sexo == 'Total general'").groupby('localidad', as_index=False)["tasa_por_100000"].sum().sort_values("tasa_por_100000", ascending=False).head()
    x = ['**{}**: {:.0f}'.format(df.iloc[i, 0].title(), df.iloc[i, 1]) for i in range(df.shape[0])]
    c2.info('\n\n'.join(x))
    
    c3.markdown("<h6 style='text-align: center; color:black;'>Mayor percepcion de vida mala y muy mala</h6>", unsafe_allow_html=True)
    df = cv_df.query("localidad != 'distrito'").groupby("condiciones_de_vida", as_index=False)["porcentaje"].mean()
    df = cv_df.query("localidad != 'distrito' & (condiciones_de_vida == 'malo' | condiciones_de_vida == 'muy malo') ").groupby("localidad", as_index=False)["porcentaje"].sum().sort_values("porcentaje", ascending=False).head()
    x = ['**{}**: {:.2f}%'.format(df.iloc[i, 0].title(), df.iloc[i, 1]) for i in range(df.shape[0])]
    c3.info('\n\n'.join(x))
    
    if datos == "Condiciones de Vida":
    
    # --------------------------
        st.markdown("<h2 style='text-align: center; color: black;'>Porcentaje promedio de condiciones de vida total en Bogotá</h2>", unsafe_allow_html=True)
        
        # Creación del dataset
        df = cv_df.groupby(['condiciones_de_vida'], as_index=False)[['porcentaje']].mean()
        
        # Creación de gráfica
        fig = px.pie(df, values='porcentaje', names='condiciones_de_vida',
               # title='<b>Porcentaje promedio de condiciones de vida total en Bogotá<b>',
               color_discrete_sequence=px.colors.qualitative.Safe, opacity=1, hover_data={'condiciones_de_vida':False, 'porcentaje':False},)
        
        # Agregar detalles a gráfica
        fig.update_layout(title=dict(x=0.5), paper_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(legendgrouptitle=dict(text='<b>Condición de vida</b><br>'), marker=dict(line=dict(color='black',width=1.3)),
                    textinfo='percent', textfont=dict(color='black'))
        
        
        st.plotly_chart(fig)
        
        # ---------
        
        st.markdown("<h2 style='text-align: center; color:black;'>Relación entre el puntaje de percepción de vida mala y muy mala con la tasa de casos de violencia por cada 100K habitantes</h2>", unsafe_allow_html=True)
        
        # Creación del dataset
        _1 = vi_df.query("year == 2017 & localidad != 'distrito' & sexo == 'Total general' & tipo_de_violencia != 'Intrafamiliar'").groupby('localidad', as_index=False)[['tasa_por_100000', 'poblacion']].agg('sum', lambda x: set(x))
        
        _2 = cv_df[cv_df['condiciones_de_vida'].isin(['malo', 'muy malo'])].groupby('localidad', as_index=False)['porcentaje'].sum()
        
        df = pd.merge(_1, _2, on='localidad', how='inner')
        
        # Creación de gráfica
        fig = px.scatter(df, y='porcentaje', x='tasa_por_100000', color='localidad', size='poblacion', template='plotly_white',
                        labels={'tasa_por_100000':'<b>Tasa de casos de violencia por cada 100K habitantes</b>', 'porcentaje':'<b>Puntaje de percepción de vida</b>', 'localidad':'<b>Localidad</b><br>'},
                        hover_name='localidad', hover_data={'localidad':False}, trendline='ols', trendline_scope='overall',
                        trendline_color_override='black', color_discrete_sequence=px.colors.qualitative.Alphabet, 
                        # title='<b>Relación entre el puntaje de percepción de vida mala y muy mala<br>con la tasa de casos de violencia por cada 100K habitantes</b>', 
                        )
        
        # Agregar detalles a gráfica
        fig.update_layout(title={'x':0.5}, paper_bgcolor='rgba(0,0,0,0)',)
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br><br>Tasa=%{x:.1f}<br>Puntaje=%{y}%<br>Población=%{marker.size}<extra></extra>')
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        
        
        fig.data[-1]['showlegend'] = False
        fig.data[-1]['hovertemplate'] = '<extra></extra>'
                
        st.plotly_chart(fig)
        st.latex(r"\rho={}".format(round(df.corr().loc['porcentaje', 'tasa_por_100000'], 2))) 
    
    
    # -----------------------
    elif datos == "Suicidios":
        # -------------------
        # c1, c2 = st.columns((1,1))
        
        st.markdown("<h2 style='text-align: center; color:black;'>Proporción de suicidios por grupo etario y género</h2>", unsafe_allow_html=True)
        # Creación del dataset
        df = sc_df[sc_df['grupo_de_edad'] != 'Todos los grupos'].groupby(['grupo_etario', 'sexo'], as_index=False)[['casos']].sum()
        
        # Creación de gráfica
        fig = px.sunburst(df, path=['grupo_etario', 'sexo'], values='casos', color='grupo_etario', maxdepth=-1, color_discrete_sequence=px.colors.qualitative.T10,
                        hover_name='grupo_etario',  hover_data={'grupo_etario':False,}, 
                        # title='<b>Proporción de suicidios por grupo etario y género</b>',
                        width=720, height=600)
        # Agregar detalles a gráfica
        fig.update_layout(title_x=0.5, paper_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(textinfo='label+percent parent')
        fig.update_traces(hovertemplate='<b>%{id}</b><br><b>Suicidios</b>: %{value}<extra></extra>')
        
        st.plotly_chart(fig)
        
        if st.checkbox("Ver Detalle"):
            c1, c2 = st.columns((1,1))
            
            gen = c1.radio("Escoja Genero", df["sexo"].unique())
            gpe = c2.radio("Escoja Grupo de Edad", df["grupo_etario"].unique())
            
            df = sc_df.loc[(sc_df['grupo_de_edad'] != 'Todos los grupos') & (sc_df['grupo_etario'] == gpe) & (sc_df['sexo'] == gen)].groupby(['grupo_de_edad', 'year'], as_index=False)[['casos']].sum()
            
            # Creación de gráfica
            fig = px.bar(df, x='grupo_de_edad', y='casos', animation_frame='year', 
                        # title='<b>Evolucion de Suicidios por Grupo de edad y genero<b>', 
                        text='casos', template='plotly_white', range_y=[0, df['casos'].max()+20],
                        color_discrete_sequence=['#EA380C'], labels={'casos':'<b>Casos</b>', 'grupo_de_edad':'<b>Grupo de edad</b>', 'year':'<b>Año<b>'},
                        hover_data={'grupo_de_edad':False, 'casos':False, 'year':False}, hover_name='year')
            
            # Agregar detalles a gráfica
            fig.update_layout(title=dict(x=0.5))
            fig.update_traces(textposition='outside')
            
            for i in fig.frames:
                i['data'][0]['textposition'] = 'outside'
                
            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
            fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500
                
            st.plotly_chart(fig)
        
            html_bytes = get_img_download_link(fig)
            
            st.download_button(label='Descargar HTML', data=html_bytes, file_name='fig.html', mime='text/html')
        
        
            # ---------
        
        st.markdown("<h2 style='text-align: center; color:black;'>Evolución anual de la tasa de suicidios por cada 100k habitantes por localidad</h2>", unsafe_allow_html=True)
        # Creación del dataset
        df = sc_df[(sc_df['grupo_de_edad'] == 'Todos los grupos') & (sc_df['localidad'] != 'distrito')].groupby(['year', 'localidad'], as_index=False)[['poblacion', 'tasa_por_100000']].agg('sum', 'mean')
        
        # Creación de gráfica
        fig = px.line(df, x='year', y='tasa_por_100000', facet_col='localidad', facet_col_wrap=5, markers=True,
                 # title='<b>Evolución anual de la tasa de suicidios por cada 100k habitantes por localidad<b>', 
                 template='plotly_white',
                 labels={'year':'<b>Año</b>', 'tasa_por_100000':'<b>Tasa por<br>100K habs</b>'}, color_discrete_sequence=['lightskyblue'], hover_name='localidad',
                 range_y=[-2, (df['tasa_por_100000'].max() + 5)])
        
        # Agregar detalles a gráfica
        fig.for_each_annotation(lambda a: a.update(text=a.text.title().split("=")[-1]))
        fig.for_each_trace(lambda x: x.update(hovertemplate='<b>%{hovertext}</b><br><b>Año</b>=%{x}<br><b>Tasa</b>=%{y:.3}<extra></extra>')) 
        fig.update_layout(title=dict(x=0.5), paper_bgcolor='rgba(0,0,0,0)')
        fig.update_xaxes(showgrid=False, showline=False, fixedrange=True, nticks=df['year'].nunique()+1)
        
        st.plotly_chart(fig)
        
        if st.checkbox("Ver localidad"):
            lc = st.selectbox("Elegir localidad", [i.title() for i in df["localidad"].unique()])
            # -------------
            df = sc_df[(sc_df['grupo_de_edad'] == 'Todos los grupos') & (sc_df['localidad'] == lc.lower())].groupby(['year', 'localidad'], as_index=False)[['poblacion', 'tasa_por_100000']].agg('sum', 'mean')
            
            # Creación de gráfica
            fig = px.line(df, x='year', y='tasa_por_100000', markers=True,
                      title=f'<b>{lc}<b>', 
                     template='plotly_white',
                     labels={'year':'<b>Año</b>', 'tasa_por_100000':'<b>Tasa por<br>100K habs</b>'}, color_discrete_sequence=['lightskyblue'], hover_name='localidad',
                     range_y=[-2, (df['tasa_por_100000'].max() + 5)])
            
            # Agregar detalles a gráfica
           
            fig.for_each_trace(lambda x: x.update(hovertemplate='<b>%{hovertext}</b><br><b>Año</b>=%{x}<br><b>Tasa</b>=%{y:.3}<extra></extra>')) 
            fig.update_layout(title=dict(x=0.5), paper_bgcolor='rgba(0,0,0,0)')
            fig.update_xaxes(showgrid=False, showline=False, fixedrange=True, nticks=df['year'].nunique()+1)
            
            st.plotly_chart(fig)
            
            # ---------------------
            
        
        
        st.markdown("<h2 style='text-align: center; color:black;'>Casos anuales de suicidio</h2>", unsafe_allow_html=True)
        # Creación del dataset
        df = sc_df.query("localidad == 'distrito' & grupo_de_edad == 'Todos los grupos'").groupby('year', as_index=False)['casos'].sum()
        df['acum'] = df['casos'].cumsum()
        
        # Creación de gráfica
        fig = px.line(df, x='year', y='casos', markers=True, template='plotly_white', text='casos',
                     labels={'casos':'<b>Casos de suicidio</b>', 'year':'<b>Año</b>'}, 
                     # title='<b>Casos anuales de suicidio<b>',
                     color_discrete_sequence=['rgba(30, 124, 55, 0.55)'], hover_data={'year':False, 'casos':False},)
        
        # Agregar detalles a gráfica
        fig.update_layout(title={'x':0.5}, paper_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(textposition='top left', textfont={'size':16})
        fig.update_xaxes(showgrid=False, fixedrange=True)
        fig.update_yaxes(showgrid=False)
        
        st.plotly_chart(fig)
        
        # ------------------
        st.markdown("<h2 style='text-align: center; color:black;'>Pareto suicidios por año</h2>", unsafe_allow_html=True)
        
        # Creación del dataset
        df = sc_df.query("grupo_de_edad == 'Todos los grupos' & localidad == 'distrito'").groupby('year', as_index=False)[['casos']].sum().sort_values('casos', ascending=False)
        df['porcentaje'] = df[['casos']].apply(lambda x: x.cumsum()/x.sum())
        df['year'] = df['year'].astype('string')
        
        # Creación de gráfica
        fig = go.Figure([go.Bar(x=df['year'], y=df['casos'], yaxis='y1', name='Suicidios', marker={'color':'rgba(182, 131, 227, 0.88)'}),
                         go.Scatter(x=df['year'], y=df['porcentaje'], yaxis='y2', name='Porcentaje', hovertemplate='%{y:.1%}', marker={'color': '#000000'})])
        
        # Agregar detalles a gráfica
        fig.update_layout(template='plotly_white', showlegend=False, hovermode='x', bargap=.3, paper_bgcolor='rgba(0,0,0,0)',
                          # title={'text': '<b>Pareto suicidios por año<b>', 'x': .5}, 
                          yaxis={'title': '<b>Suicidios</b>', 'showgrid':False, 'fixedrange':True}, xaxis={'fixedrange':True},
                          yaxis2={'fixedrange':True, 'showgrid':False, 'rangemode': "tozero", 'overlaying': 'y', 'position': 1, 'side': 'right', 'title': '<b>Porcentaje</b>', 'tickvals': np.arange(0, 1.1, .2), 'tickmode': 'array', 'ticktext': [str(i) + '%' for i in range(0, 101, 20)]})
        
        st.plotly_chart(fig)
        
        # ----------------

       
        st.markdown("<h2 style='text-align: center; color:black;'>Correlación Suicidios-Violencia</h2>", unsafe_allow_html=True)
         
        # Creación del dataset
        _1 = sc_df.query("localidad != 'distrito' & grupo_de_edad == 'Todos los grupos'").groupby(['year', 'localidad'], as_index=False)['casos'].sum()
        
        _2 = vi_df.query("localidad != 'distrito' & sexo == 'Total general' & tipo_de_violencia != 'Intrafamiliar'").groupby(['year', 'localidad'], as_index=False)[['no_casos', 'poblacion']].agg('mean', lambda x: set(x))
        
        df = pd.merge(_1, _2, on=['localidad', 'year'], how='inner').rename(columns={'casos':'suicidios', 'no_casos':'violencia'})
        
        # Creación de gráfica
        fig = px.scatter(df, y='suicidios', x='violencia', color='localidad', animation_frame='year', size='poblacion',
                        color_discrete_sequence=px.colors.qualitative.Dark2, labels={'localidad':'<b>Localidad</b><br>', 'suicidios':'<b>Casos de suicidio</b>', 'violencia':'<b>Casos de violencia</b>', 'year':'Año'}, 
                        template='plotly_white', hover_name='localidad', hover_data={'localidad':False, 'year':False, 'violencia':True, 'suicidios':True},
                        range_x=[-1, df['violencia'].max() + 80], range_y=[0.3, df['suicidios'].max() + 3], trendline='ols', trendline_scope='overall',
                        trendline_color_override='black')
        
        # Agregado de detalles y línea de tendencia a todos los frames de la gráfica
        for i,j in zip(df['year'].unique(), fig.frames):
            df = df.copy()
            df_1 = df[df['year'] == i]
            j.data = px.scatter(df_1, y='suicidios', x='violencia', color='localidad', size='poblacion',
                                color_discrete_sequence=px.colors.qualitative.Dark2, labels={'localidad':'<b>Localidad</b><br>', 'suicidios':'<b>Casos de suicidio</b>', 'violencia':'<b>Casos de violencia</b>', 'year':'Año'}, 
                                template='plotly_white', hover_name='localidad', hover_data={'localidad':False, 'year':False, 'violencia':True, 'suicidios':True},
                                trendline='ols', trendline_scope='overall', trendline_color_override='black').data
            # j.layout['annotations'] = [{'text':r"$\rho={}$".format(round(df.groupby('year').corr().loc[(i,'suicidios'), 'violencia'], 2)), 'showarrow':False,
            #                             'font':{'size':13}, 'x':110, 'y':55}]
        
        # Agregar detalles a gráfica
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        
        # fig.update_layout(annotations=[{'text':r"$\rho={}$".format(round(df.groupby('year').corr().loc[(2015,'suicidios'), 'violencia'], 2)), 'showarrow':False,
        #                                 'font':{'size':13}, 'x':110, 'y':55}], paper_bgcolor='rgba(0,0,0,0)')
        
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br><br>Casos de violencia=%{x:.3s}<br>Casos de suicidio=%{y}<br>Población=%{marker.size:}<extra></extra>')
        fig.data[-1]['showlegend'] = False
        fig.data[-1]['hovertemplate'] = '<extra></extra>'
        
        for x in fig.frames:
            for i in x.data:
                i['hovertemplate'] = '<b>%{hovertext}</b><br><br>Casos de violencia=%{x:.3s}<br>Casos de suicidio=%{y}<br>Población=%{marker.size:}<extra></extra>'
        
        fig.layout.sliders[0]['currentvalue']['prefix'] = '<b>Año</b>:'
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
        fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500
        
        for i in fig.frames:
            i.data[-1]['showlegend'] = False
            i.data[-1]['hovertemplate'] = '<extra></extra>'
            
       
        st.plotly_chart(fig)
        
        # if st.checkbox("Ver Valor de Correlación"):
        yr = st.slider("Año", int(df['year'].min()), int(df['year'].max()))
        st.latex(r"\rho={}".format(round(df.groupby('year').corr().loc[(yr,'suicidios'), 'violencia'], 2)))
        
        
        
        html_bytes = get_img_download_link(fig)
        
        st.download_button(label='Descargar HTML', data=html_bytes, file_name='fig.html', mime='text/html')
        
    elif datos == 'Violencia':
       
        
        # ---------
        c1, c2 = st.columns((1.5,1))
        
        
        c1.markdown("<h3 style='text-align: center; color:black;'>Evolución de casos por cada tipo de violencia a través de los años</h3>", unsafe_allow_html=True)
        
        # Creación del dataset
        df = vi_df[(vi_df['localidad'] != 'distrito') & (vi_df['sexo'] != 'Total general') & (vi_df['tipo_de_violencia'] != 'Intrafamiliar')]
        df = df.groupby(['tipo_de_violencia', 'year'], as_index=False)[['no_casos']].sum()
        df['tipo_de_violencia'].unique()
        
        # Creación de gráfica
        fig = px.line(df, x='year', y='no_casos', color='tipo_de_violencia',
                    labels={'no_casos':'<b>Casos<b>', 'tipo_de_violencia': '<b>Tipo de violencia<b>', 'year':'<b>Año<b>'}, 
                    template='plotly_white', 
                    # title='<b>Evolución de casos por cada tipo de violencia a través de los años<b>',
                    markers=True, color_discrete_sequence=px.colors.qualitative.Bold,
                    width=410)
        
        # Agregar detalles a gráfica
        fig.update_layout(title=dict(x=0.5), xaxis={'showgrid':False}, paper_bgcolor='rgba(0,0,0,0)', legend={'orientation':'h', 'y':-0.25})
        
        c1.plotly_chart(fig)
        
        
        # --------------
        c2.markdown("<h3 style='text-align: center; color:black;'>Porcentaje de tipos de violencia en Bogotá</h3>", unsafe_allow_html=True)
        # Creación del dataset
        df = vi_df.query("sexo == 'Total general' & localidad == 'distrito' & tipo_de_violencia != 'Intrafamiliar'").groupby('tipo_de_violencia', as_index=False)[['no_casos']].sum()
        
        # Creación de gráfica
        fig = px.pie(df, values='no_casos', names='tipo_de_violencia', 
                     # title='<b>Porcentaje de tipos de violencia en Bogotá</b>',
                     color_discrete_sequence=px.colors.qualitative.Vivid, hover_name='tipo_de_violencia', hole=0.5,
                     width=440)
        
        # Agregar detalles a gráfica
        fig.update_traces(legendgrouptitle={'text':'<b>Tipo de violencia</b><br>'}, marker={'line':{'color':'white', 'width':1.5}},
                         textfont={'color':'white'}, hovertemplate='<b>%{hovertext}</b><br>Casos:%{value:.2s}<extra></extra>',
                         textposition='inside')
        fig.update_layout(title=dict(x=0.5), legend={'orientation':'v', 'title':{'side':'left'}, 'x':-0.45}, paper_bgcolor='rgba(0,0,0,0)',
                         annotations=[{'text':f'<b>Total<br>{int(df["no_casos"].sum())}</b>', 'showarrow':False, 'font':{'size':25}}])
        
        c2.plotly_chart(fig)
        
        # ----------------------
        st.markdown("<h2 style='text-align: center; color:black;'>Violencia intrafamiliar sufrida por género</h2>", unsafe_allow_html=True)
        
        
        df = vi_df[vi_df['sexo'] != 'Total general'].groupby(['sexo', 'year'], as_index=False)[['no_casos']].sum()
        df['year'] = df['year'].astype('category')
        
        # Creación de gráfica
        fig = px.line(df, x='year', y='no_casos', color='sexo', markers=True, symbol='sexo', template='plotly_white',
                    labels={'no_casos':'<b>Casos</b>', 'year':'<b>Año</b>', 'sexo':'Genero'}, 
                    # title='<b>Violencia intrafamiliar sufrida por género</b>', 
                    hover_name='year', hover_data={'sexo':False, 'year':False})
        
        # Agregar detalles a gráfica
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br><b>Casos</b>=%{y}<extra></extra>')
        fig.update_layout(xaxis=dict(showline=False, showgrid=False), title=dict(x=0.5), paper_bgcolor='rgba(0,0,0,0)')
        fig.update_xaxes(fixedrange=True)
    
        st.plotly_chart(fig)
        
        # ------
        c1, c2 = st.columns((1.5,1))
        
        
        
        c1.markdown("<h2 style='text-align: center; color:black;'>Choropleth casos de violencia en Bogotá</h2>", unsafe_allow_html=True)
        
        with open('localidades.geojson') as f:
            geo_loc = geojson.load(f)
        
        
        token_map = "pk.eyJ1IjoibGd1ZXJyYTk4IiwiYSI6ImNsN2lhMGNtNDA3ejgzcG1nemR4Y2ZxYTIifQ.wlJDWx5tpLd2wNBW1dL0iA"
        px.set_mapbox_access_token(token_map)  
        
        df = vi_df.query("sexo == 'Total general' & localidad != 'distrito'").groupby('localidad', as_index=False)['no_casos'].sum()
        df['localidad'] = df['localidad'].replace({'la candelaria': 'candelaria', 'antonio narino': 'anotonio nariño'}).str.upper()
        
        
        
        _max = df['no_casos'].max()
        _min = df['no_casos'].min()
        
        
        fig = px.choropleth_mapbox(df, geojson = geo_loc, color = 'no_casos', locations = 'localidad', featureidkey = 'properties.Nombre de la localidad',
                      color_continuous_scale ='Viridis', range_color =(_max, _min), hover_name = 'localidad', center = {'lat':4.2629, 'lon':-74.107807}, 
                      zoom = 7.5, mapbox_style="carto-positron", labels={'no_casos': '<b>Total de casos</b>'}, hover_data={'localidad':False},
                      width=400) 
        
        fig.layout['coloraxis']['colorbar']['title']['text'] = '<b>Total<br>Casos</b>'
        
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br>Total de casos = %{z}<extra></extra>')
        
        fig.update_geos(fitbounds = 'locations', visible = True)
            
        c1.plotly_chart(fig)
        
        c2.markdown("<h2 style='text-align: right; color:black;'>Localidades con mayor cantidad de casos</h2>", unsafe_allow_html=True)
        
        df2 = df.sort_values('no_casos', ascending=False).head().rename(columns={'localidad':'Localidad', 'no_casos':'Casos'})
        
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df2.columns),
            fill_color='lightgrey',
            line_color='darkslategray'),
            cells=dict(values=[df2[i] for i in df2.columns],fill_color='white',line_color='lightgrey'))
           ])
        fig.update_layout(width=400, height=400)
        
        c2.write(fig)
        
        # ---------
       
        st.markdown("<h2 style='text-align: center; color:black;'>Correlación Suicidios-Violencia</h2>", unsafe_allow_html=True)
         
        # Creación del dataset
        _1 = sc_df.query("localidad != 'distrito' & grupo_de_edad == 'Todos los grupos'").groupby(['year', 'localidad'], as_index=False)['casos'].sum()
        
        _2 = vi_df.query("localidad != 'distrito' & sexo == 'Total general' & tipo_de_violencia != 'Intrafamiliar'").groupby(['year', 'localidad'], as_index=False)[['no_casos', 'poblacion']].agg('mean', lambda x: set(x))
        
        df = pd.merge(_1, _2, on=['localidad', 'year'], how='inner').rename(columns={'casos':'suicidios', 'no_casos':'violencia'})
        
        # Creación de gráfica
        fig = px.scatter(df, y='suicidios', x='violencia', color='localidad', animation_frame='year', size='poblacion',
                        color_discrete_sequence=px.colors.qualitative.Dark2, labels={'localidad':'<b>Localidad</b><br>', 'suicidios':'<b>Casos de suicidio</b>', 'violencia':'<b>Casos de violencia</b>', 'year':'Año'}, 
                        template='plotly_white', hover_name='localidad', hover_data={'localidad':False, 'year':False, 'violencia':True, 'suicidios':True},
                        range_x=[-1, df['violencia'].max() + 80], range_y=[0.3, df['suicidios'].max() + 3], trendline='ols', trendline_scope='overall',
                        trendline_color_override='black')
        
        # Agregado de detalles y línea de tendencia a todos los frames de la gráfica
        for i,j in zip(df['year'].unique(), fig.frames):
            df = df.copy()
            df_1 = df[df['year'] == i]
            j.data = px.scatter(df_1, y='suicidios', x='violencia', color='localidad', size='poblacion',
                                color_discrete_sequence=px.colors.qualitative.Dark2, labels={'localidad':'<b>Localidad</b><br>', 'suicidios':'<b>Casos de suicidio</b>', 'violencia':'<b>Casos de violencia</b>', 'year':'Año'}, 
                                template='plotly_white', hover_name='localidad', hover_data={'localidad':False, 'year':False, 'violencia':True, 'suicidios':True},
                                trendline='ols', trendline_scope='overall', trendline_color_override='black').data
            # j.layout['annotations'] = [{'text':r"$\rho={}$".format(round(df.groupby('year').corr().loc[(i,'suicidios'), 'violencia'], 2)), 'showarrow':False,
            #                             'font':{'size':13}, 'x':110, 'y':55}]
        
        # Agregar detalles a gráfica
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        
        # fig.update_layout(annotations=[{'text':r"$\rho={}$".format(round(df.groupby('year').corr().loc[(2015,'suicidios'), 'violencia'], 2)), 'showarrow':False,
        #                                 'font':{'size':13}, 'x':110, 'y':55}], paper_bgcolor='rgba(0,0,0,0)')
        
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br><br>Casos de violencia=%{x:.3s}<br>Casos de suicidio=%{y}<br>Población=%{marker.size:}<extra></extra>')
        fig.data[-1]['showlegend'] = False
        fig.data[-1]['hovertemplate'] = '<extra></extra>'
        
        for x in fig.frames:
            for i in x.data:
                i['hovertemplate'] = '<b>%{hovertext}</b><br><br>Casos de violencia=%{x:.3s}<br>Casos de suicidio=%{y}<br>Población=%{marker.size:}<extra></extra>'
        
        fig.layout.sliders[0]['currentvalue']['prefix'] = '<b>Año</b>:'
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
        fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500
        
        for i in fig.frames:
            i.data[-1]['showlegend'] = False
            i.data[-1]['hovertemplate'] = '<extra></extra>'
            
       
        st.plotly_chart(fig)
        
        # if st.checkbox("Ver Valor de Correlación"):
        yr = st.slider("Año", int(df['year'].min()), int(df['year'].max()))
        st.latex(r"\rho={}".format(round(df.groupby('year').corr().loc[(yr,'suicidios'), 'violencia'], 2)))
        
        
        
        html_bytes = get_img_download_link(fig)
        
        st.download_button(label='Descargar HTML', data=html_bytes, file_name='fig.html', mime='text/html')
        # ---------
        
        st.markdown("<h2 style='text-align: center; color:black;'>Relación entre el puntaje de percepción de vida mala y muy mala con la tasa de casos de violencia por cada 100K habitantes</h2>", unsafe_allow_html=True)
        
        # Creación del dataset
        _1 = vi_df.query("year == 2017 & localidad != 'distrito' & sexo == 'Total general' & tipo_de_violencia != 'Intrafamiliar'").groupby('localidad', as_index=False)[['tasa_por_100000', 'poblacion']].agg('sum', lambda x: set(x))
        
        _2 = cv_df[cv_df['condiciones_de_vida'].isin(['malo', 'muy malo'])].groupby('localidad', as_index=False)['porcentaje'].sum()
        
        df = pd.merge(_1, _2, on='localidad', how='inner')
        
        # Creación de gráfica
        fig = px.scatter(df, y='porcentaje', x='tasa_por_100000', color='localidad', size='poblacion', template='plotly_white',
                        labels={'tasa_por_100000':'<b>Tasa de casos de violencia por cada 100K habitantes</b>', 'porcentaje':'<b>Puntaje de percepción de vida</b>', 'localidad':'<b>Localidad</b><br>'},
                        hover_name='localidad', hover_data={'localidad':False}, trendline='ols', trendline_scope='overall',
                        trendline_color_override='black', color_discrete_sequence=px.colors.qualitative.Alphabet, 
                        # title='<b>Relación entre el puntaje de percepción de vida mala y muy mala<br>con la tasa de casos de violencia por cada 100K habitantes</b>', 
                        )
        
        # Agregar detalles a gráfica
        fig.update_layout(title={'x':0.5}, paper_bgcolor='rgba(0,0,0,0)',)
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br><br>Tasa=%{x:.1f}<br>Puntaje=%{y}%<br>Población=%{marker.size}<extra></extra>')
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        
        
        fig.data[-1]['showlegend'] = False
        fig.data[-1]['hovertemplate'] = '<extra></extra>'
                
        st.plotly_chart(fig)
        st.latex(r"\rho={}".format(round(df.corr().loc['porcentaje', 'tasa_por_100000'], 2)))    
    
    else:
        # --------------------------
        st.markdown("<h2 style='text-align: center; color: black;'>Porcentaje promedio de condiciones de vida total en Bogotá</h2>", unsafe_allow_html=True)
        
        # Creación del dataset
        df = cv_df.groupby(['condiciones_de_vida'], as_index=False)[['porcentaje']].mean()
        
        # Creación de gráfica
        fig = px.pie(df, values='porcentaje', names='condiciones_de_vida',
               # title='<b>Porcentaje promedio de condiciones de vida total en Bogotá<b>',
               color_discrete_sequence=px.colors.qualitative.Safe, opacity=1, hover_data={'condiciones_de_vida':False, 'porcentaje':False},)
        
        # Agregar detalles a gráfica
        fig.update_layout(title=dict(x=0.5), paper_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(legendgrouptitle=dict(text='<b>Condición de vida</b><br>'), marker=dict(line=dict(color='black',width=1.3)),
                    textinfo='percent', textfont=dict(color='black'))
        
        
        st.plotly_chart(fig)
        
        # -------------------
        # c1, c2 = st.columns((1,1))
        
        st.markdown("<h2 style='text-align: center; color:black;'>Proporción de suicidios por grupo etario y género</h2>", unsafe_allow_html=True)
        # Creación del dataset
        df = sc_df[sc_df['grupo_de_edad'] != 'Todos los grupos'].groupby(['grupo_etario', 'sexo'], as_index=False)[['casos']].sum()
        
        # Creación de gráfica
        fig = px.sunburst(df, path=['grupo_etario', 'sexo'], values='casos', color='grupo_etario', maxdepth=-1, color_discrete_sequence=px.colors.qualitative.T10,
                        hover_name='grupo_etario',  hover_data={'grupo_etario':False,}, 
                        # title='<b>Proporción de suicidios por grupo etario y género</b>',
                        width=720, height=600)
        # Agregar detalles a gráfica
        fig.update_layout(title_x=0.5, paper_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(textinfo='label+percent parent')
        fig.update_traces(hovertemplate='<b>%{id}</b><br><b>Suicidios</b>: %{value}<extra></extra>')
        
        st.plotly_chart(fig)
        
        if st.checkbox("Ver Detalle"):
            c1, c2 = st.columns((1,1))
            
            gen = c1.radio("Escoja Genero", df["sexo"].unique())
            gpe = c2.radio("Escoja Grupo de Edad", df["grupo_etario"].unique())
            
            df = sc_df.loc[(sc_df['grupo_de_edad'] != 'Todos los grupos') & (sc_df['grupo_etario'] == gpe) & (sc_df['sexo'] == gen)].groupby(['grupo_de_edad', 'year'], as_index=False)[['casos']].sum()
            
            # Creación de gráfica
            fig = px.bar(df, x='grupo_de_edad', y='casos', animation_frame='year', 
                        # title='<b>Evolucion de Suicidios por Grupo de edad y genero<b>', 
                        text='casos', template='plotly_white', range_y=[0, df['casos'].max()+20],
                        color_discrete_sequence=['#EA380C'], labels={'casos':'<b>Casos</b>', 'grupo_de_edad':'<b>Grupo de edad</b>', 'year':'<b>Año<b>'},
                        hover_data={'grupo_de_edad':False, 'casos':False, 'year':False}, hover_name='year')
            
            # Agregar detalles a gráfica
            fig.update_layout(title=dict(x=0.5))
            fig.update_traces(textposition='outside')
            
            for i in fig.frames:
                i['data'][0]['textposition'] = 'outside'
                
            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
            fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500
                
            st.plotly_chart(fig)
        
            html_bytes = get_img_download_link(fig)
            
            st.download_button(label='Descargar HTML', data=html_bytes, file_name='fig.html', mime='text/html')
        
        
            # ---------
        
        st.markdown("<h2 style='text-align: center; color:black;'>Evolución anual de la tasa de suicidios por cada 100k habitantes por localidad</h2>", unsafe_allow_html=True)
        # Creación del dataset
        df = sc_df[(sc_df['grupo_de_edad'] == 'Todos los grupos') & (sc_df['localidad'] != 'distrito')].groupby(['year', 'localidad'], as_index=False)[['poblacion', 'tasa_por_100000']].agg('sum', 'mean')
        
        # Creación de gráfica
        fig = px.line(df, x='year', y='tasa_por_100000', facet_col='localidad', facet_col_wrap=5, markers=True,
                 # title='<b>Evolución anual de la tasa de suicidios por cada 100k habitantes por localidad<b>', 
                 template='plotly_white',
                 labels={'year':'<b>Año</b>', 'tasa_por_100000':'<b>Tasa por<br>100K habs</b>'}, color_discrete_sequence=['lightskyblue'], hover_name='localidad',
                 range_y=[-2, (df['tasa_por_100000'].max() + 5)])
        
        # Agregar detalles a gráfica
        fig.for_each_annotation(lambda a: a.update(text=a.text.title().split("=")[-1]))
        fig.for_each_trace(lambda x: x.update(hovertemplate='<b>%{hovertext}</b><br><b>Año</b>=%{x}<br><b>Tasa</b>=%{y:.3}<extra></extra>')) 
        fig.update_layout(title=dict(x=0.5), paper_bgcolor='rgba(0,0,0,0)')
        fig.update_xaxes(showgrid=False, showline=False, fixedrange=True, nticks=df['year'].nunique()+1)
        
        st.plotly_chart(fig)
        
        if st.checkbox("Ver localidad"):
            lc = st.selectbox("Elegir localidad", [i.title() for i in df["localidad"].unique()])
            # -------------
            df = sc_df[(sc_df['grupo_de_edad'] == 'Todos los grupos') & (sc_df['localidad'] == lc.lower())].groupby(['year', 'localidad'], as_index=False)[['poblacion', 'tasa_por_100000']].agg('sum', 'mean')
            
            # Creación de gráfica
            fig = px.line(df, x='year', y='tasa_por_100000', markers=True,
                      title=f'<b>{lc}<b>', 
                     template='plotly_white',
                     labels={'year':'<b>Año</b>', 'tasa_por_100000':'<b>Tasa por<br>100K habs</b>'}, color_discrete_sequence=['lightskyblue'], hover_name='localidad',
                     range_y=[-2, (df['tasa_por_100000'].max() + 5)])
            
            # Agregar detalles a gráfica
           
            fig.for_each_trace(lambda x: x.update(hovertemplate='<b>%{hovertext}</b><br><b>Año</b>=%{x}<br><b>Tasa</b>=%{y:.3}<extra></extra>')) 
            fig.update_layout(title=dict(x=0.5), paper_bgcolor='rgba(0,0,0,0)')
            fig.update_xaxes(showgrid=False, showline=False, fixedrange=True, nticks=df['year'].nunique()+1)
            
            st.plotly_chart(fig)
        
        # ---------------------
            
        
        
        st.markdown("<h2 style='text-align: center; color:black;'>Casos anuales de suicidio</h2>", unsafe_allow_html=True)
        # Creación del dataset
        df = sc_df.query("localidad == 'distrito' & grupo_de_edad == 'Todos los grupos'").groupby('year', as_index=False)['casos'].sum()
        df['acum'] = df['casos'].cumsum()
        
        # Creación de gráfica
        fig = px.line(df, x='year', y='casos', markers=True, template='plotly_white', text='casos',
                     labels={'casos':'<b>Casos de suicidio</b>', 'year':'<b>Año</b>'}, 
                     # title='<b>Casos anuales de suicidio<b>',
                     color_discrete_sequence=['rgba(30, 124, 55, 0.55)'], hover_data={'year':False, 'casos':False},)
        
        # Agregar detalles a gráfica
        fig.update_layout(title={'x':0.5}, paper_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(textposition='top left', textfont={'size':16})
        fig.update_xaxes(showgrid=False, fixedrange=True)
        fig.update_yaxes(showgrid=False)
        
        st.plotly_chart(fig)
        
        # ------------------
        st.markdown("<h2 style='text-align: center; color:black;'>Pareto suicidios por año</h2>", unsafe_allow_html=True)
        
        # Creación del dataset
        df = sc_df.query("grupo_de_edad == 'Todos los grupos' & localidad == 'distrito'").groupby('year', as_index=False)[['casos']].sum().sort_values('casos', ascending=False)
        df['porcentaje'] = df[['casos']].apply(lambda x: x.cumsum()/x.sum())
        df['year'] = df['year'].astype('string')
        
        # Creación de gráfica
        fig = go.Figure([go.Bar(x=df['year'], y=df['casos'], yaxis='y1', name='Suicidios', marker={'color':'rgba(182, 131, 227, 0.88)'}),
                         go.Scatter(x=df['year'], y=df['porcentaje'], yaxis='y2', name='Porcentaje', hovertemplate='%{y:.1%}', marker={'color': '#000000'})])
        
        # Agregar detalles a gráfica
        fig.update_layout(template='plotly_white', showlegend=False, hovermode='x', bargap=.3, paper_bgcolor='rgba(0,0,0,0)',
                          # title={'text': '<b>Pareto suicidios por año<b>', 'x': .5}, 
                          yaxis={'title': '<b>Suicidios</b>', 'showgrid':False, 'fixedrange':True}, xaxis={'fixedrange':True},
                          yaxis2={'fixedrange':True, 'showgrid':False, 'rangemode': "tozero", 'overlaying': 'y', 'position': 1, 'side': 'right', 'title': '<b>Porcentaje</b>', 'tickvals': np.arange(0, 1.1, .2), 'tickmode': 'array', 'ticktext': [str(i) + '%' for i in range(0, 101, 20)]})
        
        st.plotly_chart(fig)
        
        
        
        # ---------
        c1, c2 = st.columns((1.5,1))
        
        
        c1.markdown("<h3 style='text-align: center; color:black;'>Evolución de casos por cada tipo de violencia a través de los años</h3>", unsafe_allow_html=True)
        
        # Creación del dataset
        df = vi_df[(vi_df['localidad'] != 'distrito') & (vi_df['sexo'] != 'Total general') & (vi_df['tipo_de_violencia'] != 'Intrafamiliar')]
        df = df.groupby(['tipo_de_violencia', 'year'], as_index=False)[['no_casos']].sum()
        df['tipo_de_violencia'].unique()
        
        # Creación de gráfica
        fig = px.line(df, x='year', y='no_casos', color='tipo_de_violencia',
                    labels={'no_casos':'<b>Casos<b>', 'tipo_de_violencia': '<b>Tipo de violencia<b>', 'year':'<b>Año<b>'}, 
                    template='plotly_white', 
                    # title='<b>Evolución de casos por cada tipo de violencia a través de los años<b>',
                    markers=True, color_discrete_sequence=px.colors.qualitative.Bold,
                    width=410)
        
        # Agregar detalles a gráfica
        fig.update_layout(title=dict(x=0.5), xaxis={'showgrid':False}, paper_bgcolor='rgba(0,0,0,0)', legend={'orientation':'h', 'y':-0.25})
        
        c1.plotly_chart(fig)
        
        
        # --------------
        c2.markdown("<h3 style='text-align: center; color:black;'>Porcentaje de tipos de violencia en Bogotá</h3>", unsafe_allow_html=True)
        # Creación del dataset
        df = vi_df.query("sexo == 'Total general' & localidad == 'distrito' & tipo_de_violencia != 'Intrafamiliar'").groupby('tipo_de_violencia', as_index=False)[['no_casos']].sum()
        
        # Creación de gráfica
        fig = px.pie(df, values='no_casos', names='tipo_de_violencia', 
                     # title='<b>Porcentaje de tipos de violencia en Bogotá</b>',
                     color_discrete_sequence=px.colors.qualitative.Vivid, hover_name='tipo_de_violencia', hole=0.5,
                     width=440)
        
        # Agregar detalles a gráfica
        fig.update_traces(legendgrouptitle={'text':'<b>Tipo de violencia</b><br>'}, marker={'line':{'color':'white', 'width':1.5}},
                         textfont={'color':'white'}, hovertemplate='<b>%{hovertext}</b><br>Casos:%{value:.2s}<extra></extra>',
                         textposition='inside')
        fig.update_layout(title=dict(x=0.5), legend={'orientation':'v', 'title':{'side':'left'}, 'x':-0.45}, paper_bgcolor='rgba(0,0,0,0)',
                         annotations=[{'text':f'<b>Total<br>{int(df["no_casos"].sum())}</b>', 'showarrow':False, 'font':{'size':25}}])
        
        c2.plotly_chart(fig)
        
        # ----------------------
        st.markdown("<h2 style='text-align: center; color:black;'>Violencia intrafamiliar sufrida por género</h2>", unsafe_allow_html=True)
        
        
        df = vi_df[vi_df['sexo'] != 'Total general'].groupby(['sexo', 'year'], as_index=False)[['no_casos']].sum()
        df['year'] = df['year'].astype('category')
        
        # Creación de gráfica
        fig = px.line(df, x='year', y='no_casos', color='sexo', markers=True, symbol='sexo', template='plotly_white',
                    labels={'no_casos':'<b>Casos</b>', 'year':'<b>Año</b>', 'sexo':'Genero'}, 
                    # title='<b>Violencia intrafamiliar sufrida por género</b>', 
                    hover_name='year', hover_data={'sexo':False, 'year':False})
        
        # Agregar detalles a gráfica
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br><b>Casos</b>=%{y}<extra></extra>')
        fig.update_layout(xaxis=dict(showline=False, showgrid=False), title=dict(x=0.5), paper_bgcolor='rgba(0,0,0,0)')
        fig.update_xaxes(fixedrange=True)
    
        st.plotly_chart(fig)
        
        
        
        # ------
        c1, c2 = st.columns((1.5,1))
        
        
        
        c1.markdown("<h2 style='text-align: center; color:black;'>Choropleth casos de violencia en Bogotá</h2>", unsafe_allow_html=True)
        
        with open('localidades.geojson') as f:
            geo_loc = geojson.load(f)
        
        
        token_map = "pk.eyJ1IjoibGd1ZXJyYTk4IiwiYSI6ImNsN2lhMGNtNDA3ejgzcG1nemR4Y2ZxYTIifQ.wlJDWx5tpLd2wNBW1dL0iA"
        px.set_mapbox_access_token(token_map)  
        
        df = vi_df.query("sexo == 'Total general' & localidad != 'distrito'").groupby('localidad', as_index=False)['no_casos'].sum()
        df['localidad'] = df['localidad'].replace({'la candelaria': 'candelaria', 'antonio narino': 'anotonio nariño'}).str.upper()
        
        
        
        _max = df['no_casos'].max()
        _min = df['no_casos'].min()
        
        
        fig = px.choropleth_mapbox(df, geojson = geo_loc, color = 'no_casos', locations = 'localidad', featureidkey = 'properties.Nombre de la localidad',
                      color_continuous_scale ='Viridis', range_color =(_max, _min), hover_name = 'localidad', center = {'lat':4.2629, 'lon':-74.107807}, 
                      zoom = 7.5, mapbox_style="carto-positron", labels={'no_casos': '<b>Total de casos</b>'}, hover_data={'localidad':False},
                      width=400) 
        
        fig.layout['coloraxis']['colorbar']['title']['text'] = '<b>Total<br>Casos</b>'
        
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br>Total de casos = %{z}<extra></extra>')
        
        fig.update_geos(fitbounds = 'locations', visible = True)
            
        c1.plotly_chart(fig)
        
        c2.markdown("<h2 style='text-align: right; color:black;'>Localidades con mayor cantidad de casos</h2>", unsafe_allow_html=True)
        
        df2 = df.sort_values('no_casos', ascending=False).head().rename(columns={'localidad':'Localidad', 'no_casos':'Casos'})
        
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df2.columns),
            fill_color='lightgrey',
            line_color='darkslategray'),
            cells=dict(values=[df2[i] for i in df2.columns],fill_color='white',line_color='lightgrey'))
           ])
        fig.update_layout(width=400, height=400)
        
        c2.write(fig)
        
        # ----------------
       
       
        st.markdown("<h2 style='text-align: center; color:black;'>Correlación Suicidios-Violencia</h2>", unsafe_allow_html=True)
         
        # Creación del dataset
        _1 = sc_df.query("localidad != 'distrito' & grupo_de_edad == 'Todos los grupos'").groupby(['year', 'localidad'], as_index=False)['casos'].sum()
        
        _2 = vi_df.query("localidad != 'distrito' & sexo == 'Total general' & tipo_de_violencia != 'Intrafamiliar'").groupby(['year', 'localidad'], as_index=False)[['no_casos', 'poblacion']].agg('mean', lambda x: set(x))
        
        df = pd.merge(_1, _2, on=['localidad', 'year'], how='inner').rename(columns={'casos':'suicidios', 'no_casos':'violencia'})
        
        # Creación de gráfica
        fig = px.scatter(df, y='suicidios', x='violencia', color='localidad', animation_frame='year', size='poblacion',
                        color_discrete_sequence=px.colors.qualitative.Dark2, labels={'localidad':'<b>Localidad</b><br>', 'suicidios':'<b>Casos de suicidio</b>', 'violencia':'<b>Casos de violencia</b>', 'year':'Año'}, 
                        template='plotly_white', hover_name='localidad', hover_data={'localidad':False, 'year':False, 'violencia':True, 'suicidios':True},
                        range_x=[-1, df['violencia'].max() + 80], range_y=[0.3, df['suicidios'].max() + 3], trendline='ols', trendline_scope='overall',
                        trendline_color_override='black')
        
        # Agregado de detalles y línea de tendencia a todos los frames de la gráfica
        for i,j in zip(df['year'].unique(), fig.frames):
            df = df.copy()
            df_1 = df[df['year'] == i]
            j.data = px.scatter(df_1, y='suicidios', x='violencia', color='localidad', size='poblacion',
                                color_discrete_sequence=px.colors.qualitative.Dark2, labels={'localidad':'<b>Localidad</b><br>', 'suicidios':'<b>Casos de suicidio</b>', 'violencia':'<b>Casos de violencia</b>', 'year':'Año'}, 
                                template='plotly_white', hover_name='localidad', hover_data={'localidad':False, 'year':False, 'violencia':True, 'suicidios':True},
                                trendline='ols', trendline_scope='overall', trendline_color_override='black').data
            # j.layout['annotations'] = [{'text':r"$\rho={}$".format(round(df.groupby('year').corr().loc[(i,'suicidios'), 'violencia'], 2)), 'showarrow':False,
            #                             'font':{'size':13}, 'x':110, 'y':55}]
        
        # Agregar detalles a gráfica
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        
        # fig.update_layout(annotations=[{'text':r"$\rho={}$".format(round(df.groupby('year').corr().loc[(2015,'suicidios'), 'violencia'], 2)), 'showarrow':False,
        #                                 'font':{'size':13}, 'x':110, 'y':55}], paper_bgcolor='rgba(0,0,0,0)')
        
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br><br>Casos de violencia=%{x:.3s}<br>Casos de suicidio=%{y}<br>Población=%{marker.size:}<extra></extra>')
        fig.data[-1]['showlegend'] = False
        fig.data[-1]['hovertemplate'] = '<extra></extra>'
        
        for x in fig.frames:
            for i in x.data:
                i['hovertemplate'] = '<b>%{hovertext}</b><br><br>Casos de violencia=%{x:.3s}<br>Casos de suicidio=%{y}<br>Población=%{marker.size:}<extra></extra>'
        
        fig.layout.sliders[0]['currentvalue']['prefix'] = '<b>Año</b>:'
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
        fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500
        
        for i in fig.frames:
            i.data[-1]['showlegend'] = False
            i.data[-1]['hovertemplate'] = '<extra></extra>'
            
       
        st.plotly_chart(fig)
        
        # if st.checkbox("Ver Valor de Correlación"):
        yr = st.slider("Año", int(df['year'].min()), int(df['year'].max()))
        st.latex(r"\rho={}".format(round(df.groupby('year').corr().loc[(yr,'suicidios'), 'violencia'], 2)))
        
        
        
        html_bytes = get_img_download_link(fig)
        
        st.download_button(label='Descargar HTML', data=html_bytes, file_name='fig.html', mime='text/html')
        
        # ---------
        
        st.markdown("<h2 style='text-align: center; color:black;'>Relación entre el puntaje de percepción de vida mala y muy mala con la tasa de casos de violencia por cada 100K habitantes</h2>", unsafe_allow_html=True)
        
        # Creación del dataset
        _1 = vi_df.query("year == 2017 & localidad != 'distrito' & sexo == 'Total general' & tipo_de_violencia != 'Intrafamiliar'").groupby('localidad', as_index=False)[['tasa_por_100000', 'poblacion']].agg('sum', lambda x: set(x))
        
        _2 = cv_df[cv_df['condiciones_de_vida'].isin(['malo', 'muy malo'])].groupby('localidad', as_index=False)['porcentaje'].sum()
        
        df = pd.merge(_1, _2, on='localidad', how='inner')
        
        # Creación de gráfica
        fig = px.scatter(df, y='porcentaje', x='tasa_por_100000', color='localidad', size='poblacion', template='plotly_white',
                        labels={'tasa_por_100000':'<b>Tasa de casos de violencia por cada 100K habitantes</b>', 'porcentaje':'<b>Puntaje de percepción de vida</b>', 'localidad':'<b>Localidad</b><br>'},
                        hover_name='localidad', hover_data={'localidad':False}, trendline='ols', trendline_scope='overall',
                        trendline_color_override='black', color_discrete_sequence=px.colors.qualitative.Alphabet, 
                        # title='<b>Relación entre el puntaje de percepción de vida mala y muy mala<br>con la tasa de casos de violencia por cada 100K habitantes</b>', 
                        )
        
        # Agregar detalles a gráfica
        fig.update_layout(title={'x':0.5}, paper_bgcolor='rgba(0,0,0,0)',)
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br><br>Tasa=%{x:.1f}<br>Puntaje=%{y}%<br>Población=%{marker.size}<extra></extra>')
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        
        
        fig.data[-1]['showlegend'] = False
        fig.data[-1]['hovertemplate'] = '<extra></extra>'
                
        st.plotly_chart(fig)
        st.latex(r"\rho={}".format(round(df.corr().loc['porcentaje', 'tasa_por_100000'], 2))) 
    
    st.title("          ")        
    st.markdown("<h5 style='text-align: left; color: blue;'>Enlaces para descarga de datos</h5>", unsafe_allow_html=True)
    
    
    c1, c2, c3 = st.columns((1,1,1))
    
    c1.download_button(label='Suicidios', data=sc_df.to_csv(), file_name='suicidios.csv', mime='text/csv')
    c2.download_button(label='Condiciones de Vida', data=cv_df.to_csv(), file_name='condiciones_de_vida.csv', mime='text/csv')
    c3.download_button(label='Violencia Intrafamiliar', data=vi_df.to_csv(), file_name='violencia_intrafamiliar.csv', mime='text/csv')
   
        
if __name__ == '__main__':
    main()














#%%
# df_1 = pd.read_csv("condicion_mod.csv")
# df = df_1.query("localidad != 'distrito'").groupby("condiciones_de_vida", as_index=False)["porcentaje"].mean().sort_values("condiciones_de_vida")
# df['order'] = df['condiciones_de_vida'].replace({'muy bueno':0, 'bueno':1, 'regular':2, 'malo':3, 'muy malo':4})
# df.sort_values('order', inplace=True)
# x = [(df.iloc[i, 0], df.iloc[i, 1]) for i in range(df.shape[0])]

# x = ['{}:{}'.format(df.iloc[i, 0].title(), df.iloc[i, 1]) for i in range(df.shape[0])]
# text = '\n'.join(x)

# print(df)
# fig.write_html("My3dPlot.html")









