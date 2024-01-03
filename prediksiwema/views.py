#view.py
from .result import result_view
from django.shortcuts import render, redirect
import plotly.graph_objects as go
from .models import Result
import pandas as pd
import numpy as np
import json
import base64
import plotly.offline as plotly
import matplotlib.pyplot as plt
import io
import plotly.io as pio
from django.http import HttpResponse
from django.contrib.sessions.backends.db import SessionStore


class ExponentialWeightedMovingAverage:
    def __init__(self, span):
        self.alpha = 2 / (span + 1)
        self.isInitialized = False
        self.averages = None

    def update(self, values):
        if self.isInitialized:
            for i in range(len(values)):
                self.averages[i] += self.alpha * (values[i] - self.averages[i])
                wema_value = self.alpha * values[i] + (1 - self.alpha) * self.averages[i]
                self.averages[i] = wema_value
        else:
            self.averages = values.copy()
            self.isInitialized = True

def convert_to_json(data):
    return json.dumps([int(value) for value in data])

def calculate_wema(request):
    if request.method == 'POST':
        span = request.POST['span']

        # Memeriksa apakah file dataset sudah diunggah
        if 'datasetFile' not in request.FILES:
            return render(request, 'input.html')

        # Mengambil file dataset yang diunggah
        dataset_file = request.FILES['datasetFile']

        # Membaca dataset dari file Excel
        try:
            df = pd.read_excel(dataset_file)
        except Exception as e:
            return HttpResponse(f"Error reading dataset file: {str(e)}")

        # Memeriksa format dataset yang diharapkan
        expected_columns = ['No.', 'Komoditas()']
        if not set(expected_columns).issubset(df.columns):
            error_message = 'Dataset tidak sesuai format.'
            return render(request, 'input.html', {'error_message': error_message})
        
        komoditas = ['Daging Ayam', 'Daging Sapi', 'Telur Ayam', 'Minyak Goreng', 'Gula Pasir']
        results = []
        chart_data = []
        df_wema = pd.DataFrame(columns=['Komoditas'] + [f'WEMA_{i+1}' for i in range(int(span))] + ['Aktual'])

        for i, kom in enumerate(komoditas, 1):
            wema = ExponentialWeightedMovingAverage(int(span) + 1)

            # values_column = df.columns[2:]
            # values = df.loc[df['Komoditas()'] == kom, values_column].values.flatten()

            values = df[df['Komoditas()'] == kom].iloc[:, 1:].values.flatten()            
            values = pd.to_numeric(values, errors='coerce')
            values = [value for value in values if not np.isnan(value)]

            wema_values = []  # Menyimpan setiap hitungan WEMA per harinya

            for value in values:
                wema.update([value])
                wema_values.append(wema.averages[-1])

            # Menambahkan baris ke dataframe df_wema
            if len(df_wema.columns) != len([kom] + wema_values + [values[-1]]):
                num_columns_to_add = len([kom] + wema_values + [values[-1]]) - len(df_wema.columns)
                new_columns = [f'WEMA_{i+1}' for i in range(num_columns_to_add)]
                df_wema = pd.concat([df_wema, pd.DataFrame(columns=new_columns)], axis=1)

            row = pd.Series([kom] + wema_values + [values[-1]], index=df_wema.columns)
            df_wema = pd.concat([df_wema, row.to_frame().T], ignore_index=True)

            # Menghitung MAPE
            actual_values = df.loc[df['Komoditas()'] == kom].iloc[:, -1:].values.flatten()
            actual_values = pd.to_numeric(actual_values, errors='coerce') # Mengonversi nilai menjadi float
            actual_values = [value for value in actual_values if not np.isnan(value)]# Menghapus nilai NaN
            # Mengambil nilai terakhir dari rata-rata WEMA sebagai nilai forecast
            forecast_values = [wema.averages[-1]] * len(actual_values)  # Mengambil nilai terakhir dari rata-rata WEMA

            # Menghitung selisih absolut untuk setiap nilai aktual
            absolute_errors = [abs(actual - forecast) for actual, forecast in zip(actual_values, forecast_values)]
            absolute_actual_values = [abs(actual) for actual in actual_values]
            
            # Menghitung MAPE dalam persentase
            mape = sum(absolute_errors) / sum(absolute_actual_values) * 100
            mape_percentage = "{:.2f}".format(mape)

            x_values = list(range(len(actual_values)))
            x_wema_values = list(range(len(actual_values), len(actual_values) + len(wema_values)))
            x_all_values = list(range(len(actual_values) + len(wema_values)))  # Tambahkan ini untuk panjang garis yang sama dengan dataset
                    
            trace_actual = go.Scatter(x=x_wema_values, y=wema_values, mode='lines+markers', name='Aktual', line=dict(color='blue'))
            trace_forecast = go.Scatter(x=x_all_values, y=[None]*len(x_values) + list(actual_values) + list(wema_values), mode='lines+markers', name='Prediksi', line=dict(color='red'))
            
            chart_data = [trace_actual, trace_forecast]
            chart_layout = go.Layout(title=f'Prediksi WEMA dan Garis Aktual untuk {kom}', xaxis=dict(title='Hari'), yaxis=dict(title='Harga'))
            chart_fig = go.Figure(data=chart_data, layout=chart_layout)

            chart_div = chart_fig.to_html(full_html=False)

            # Menyimpan hasil perhitungan ke dalam model Result
            result = Result(
                komoditas=kom,
                wema_average=wema.averages[-1],
                mape=mape,
                actual_values=convert_to_json(actual_values),
                mape_percentage=mape_percentage
            )

            # result['wema_average'] = json.dumps(result['wema_average'])
            results.append(result)    
            
        # Mengurutkan hasil berdasarkan nilai MAPE
        results.sort(key=lambda x: x.mape)

        # Konfigurasi layout grafik
        chart_layout = go.Layout(
            title="Grafik Prediksi WEMA dan Garis Aktual",
            xaxis=dict(title="Hari"),
            yaxis=dict(title="Harga"),
        )

        # Menggabungkan semua trace ke dalam chart_data
        chart_fig = go.Figure(data=chart_data, layout=chart_layout)
        chart_div = chart_fig.to_json()

        # Menghasilkan representasi HTML dari grafik
        # chart_div = chart_fig.to_html(full_html=False)
        
        Result.objects.bulk_create(results)

        # Konversi DataFrame menjadi JSON dengan orientasi 'split' dan format tanggal 'iso'
        df_wema_json = df_wema.to_json(orient='split', date_format='iso')

        # Menyimpan hasil perhitungan dalam session
        request.session['results'] = [result.__dict__ for result in results]
        request.session['span'] = span
        request.session['df_wema'] = df_wema_json

        # Menyimpan hasil perhitungan dalam session
        request.session['results'] = [
            {
                'komoditas': result.komoditas,
                'wema_average': result.wema_average,
                'mape': result.mape,
                'actual_values': result.actual_values,
                'mape_percentage': result.mape_percentage
            }
            for result in results
        ]

        # Menampilkan hasil perhitungan dan grafik yang terurut
        return render(
            request,
            "result.html",
            {'results': results,"span": span, "chart_div": chart_div},            
        )

    elif 'results' in request.session:  
        results = [Result(**result_data) for result_data in request.session['results']]
        span = request.session['span']
        return render(request, 'result.html', {'results': results, 'span': span})
    
    return redirect('calculate_wema') 
    #return HttpResponse("sukses perhitungan") 

def home(request):
    return render(request, 'input.html')   

def grafik(request):
    results = request.session.get('results', []) 
    span = request.session.get('span', 0)
    df_wema_json = request.session.get('df_wema')
    df_wema = pd.read_json(df_wema_json, orient='split')

    komoditas = ['Daging Ayam', 'Daging Sapi', 'Telur Ayam', 'Minyak Goreng', 'Gula Pasir']
    charts = []

    for kom in komoditas:
        wema_values = df_wema.loc[df_wema['Komoditas'] == kom, [col for col in df_wema.columns if col.startswith('WEMA_')]].values.flatten()
        actual_values = df_wema.loc[df_wema['Komoditas'] == kom, 'Aktual'].values
        
        x_values = list(range(len(actual_values)))
        x_wema_values = list(range(len(actual_values), len(actual_values) + len(wema_values)))
        x_all_values = list(range(len(actual_values) + len(wema_values)))

        trace_actual = go.Scatter(x=x_wema_values, y=wema_values, mode='lines+markers', name='Aktual', line=dict(color='blue'))
        trace_forecast = go.Scatter(x=x_all_values, y=[None]*len(x_values) + list(actual_values) + list(wema_values), mode='lines+markers', name='Prediksi', line=dict(color='red'))
        
        chart_data = [trace_actual, trace_forecast]
        chart_layout = go.Layout(title=f'Prediksi WEMA dan Garis Aktual untuk {kom}', xaxis=dict(title='Hari'), yaxis=dict(title='Harga'))
        chart_fig = go.Figure(data=chart_data, layout=chart_layout)

        chart_div = chart_fig.to_html(full_html=False)
        charts.append((kom, chart_div))

    return render(
        request,
        "grafik.html",
        {"charts": charts, "span": span, "results": results, "chart_div": chart_div},
    )

