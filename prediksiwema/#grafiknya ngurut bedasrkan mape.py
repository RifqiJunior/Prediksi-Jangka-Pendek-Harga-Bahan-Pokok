#grafiknya ngurut bedasrkan mape

from django.shortcuts import render
import plotly.graph_objects as go
#from .models import Result
import pandas as pd
import numpy as np
import json
import plotly.offline as plotly
from django.http import HttpResponse

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

        for i, kom in enumerate(komoditas, 1):
            wema = ExponentialWeightedMovingAverage(int(span) + 1)

            values_column = df.columns[2:]
            values = df.loc[df['Komoditas()'] == kom, values_column].values.flatten()
            values = pd.to_numeric(values, errors='coerce')
            values = [value for value in values if not np.isnan(value)]

            for value in values:
                wema.update([value])

            actual_values = df.loc[df['Komoditas()'] == kom, values_column[-1]].values.flatten()
            actual_values = pd.to_numeric(actual_values, errors='coerce')
            actual_values = [value for value in actual_values if not np.isnan(value)]

            forecast_values = [wema.averages[-1]] * len(actual_values)
            absolute_errors = [abs(actual - forecast) for actual, forecast in zip(actual_values, forecast_values)]
            percentage_errors = [error / actual * 100 for error, actual in zip(absolute_errors, actual_values)]
            mape = sum(percentage_errors) / len(percentage_errors)
            mape_percentage = "{:.2f}".format(mape * 100)

            result = Result(
                komoditas=kom,
                wema_average=wema.averages[-1],
                mape=mape,
                actual_values=convert_to_json(actual_values),
                mape_percentage=mape_percentage
            )

            results.append(result)
            
        # Mengurutkan hasil berdasarkan nilai MAPE
        results.sort(key=lambda x: x.mape)

        # Menyiapkan data untuk grafik
        chart_trace_actual = go.Bar(
            x=[result.komoditas for result in results],
            y=[result.actual_values for result in results],
            name="Actual",
        )
        chart_trace_forecast = go.Scatter(
            x=[result.komoditas for result in results],
            y=[result.wema_average for result in results],
            mode="lines",
            name="Forecast",
        )
        chart_trace_mape = go.Scatter(
            x=[result.komoditas for result in results],
            y=[result.wema_average for result in results],
            mode="markers+text",
            name="MAPE",
            text=[f"MAPE: {result.mape_percentage}%" for result in results],
            textposition="top center",
        )

        # Menambahkan semua trace ke dalam chart_data
        chart_data.append(chart_trace_actual)
        chart_data.append(chart_trace_forecast)
        chart_data.append(chart_trace_mape)

        # Konfigurasi layout grafik
        chart_layout = go.Layout(
            title="Grafik untuk Kelima Bahan Pokok",
            xaxis=dict(title="Komoditas"),
            yaxis=dict(title="Harga"),
        )

        chart_fig = go.Figure(data=chart_data, layout=chart_layout)

        # Mengurutkan hasil berdasarkan nilai MAPE secara descending (dari besar ke kecil)
        sorted_results = sorted(results, key=lambda x: x.mape, reverse=True)

        # Menyiapkan data untuk grafik dengan hasil terurut
        sorted_chart_trace_actual = go.Bar(
            x=[result.komoditas for result in sorted_results],
            y=[result.actual_values for result in sorted_results],
            name="Actual",
        )
        sorted_chart_trace_forecast = go.Scatter(
            x=[result.komoditas for result in sorted_results],
            y=[result.wema_average for result in sorted_results],
            mode="lines",
            name="Forecast",
        )
        sorted_chart_trace_mape = go.Scatter(
            x=[result.komoditas for result in sorted_results],
            y=[result.wema_average for result in sorted_results],
            mode="markers+text",
            name="MAPE",
            text=[f"MAPE: {result.mape_percentage}%" for result in sorted_results],
            textposition="top center",
        )

        # Menambahkan semua trace ke dalam chart_data yang terurut
        sorted_chart_data = []
        sorted_chart_data.append(sorted_chart_trace_actual)
        sorted_chart_data.append(sorted_chart_trace_forecast)
        sorted_chart_data.append(sorted_chart_trace_mape)

        sorted_chart_fig = go.Figure(data=sorted_chart_data, layout=chart_layout)
        sorted_chart_div = sorted_chart_fig.to_json()

        Result.objects.bulk_create(results)

        # Menampilkan hasil perhitungan dan grafik yang terurut
        return render(
            request,
            "result.html",
            {"results": sorted_results, "span": span, "chart_div": sorted_chart_div},
        )

    return render(request, 'input.html')