#grafiknya lumayan lah

from django.shortcuts import render
import plotly.graph_objects as go
from .models import Result
import pandas as pd
import numpy as np
import json
import plotly.offline as plotly
from django.http import HttpResponse
import ast

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
            return HttpResponse("Dataset tidak sesuai format.", status=400)

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
            #actual_values = [value for value in actual_values if not np.isnan(value)]
            actual_values_parsed = []
            for val in actual_values:
                try:
                    actual = ast.literal_eval(val)
                    actual_values_parsed.append(actual)
                except (ValueError, SyntaxError):
                    pass

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

           
            # Menyiapkan data untuk grafik
            chart_trace_actual = go.Bar(
                x=[result.komoditas],
                y=actual_values,
                name="Actual",
            )

            chart_trace_forecast = go.Bar(
                x=[result.komoditas],
                y=[result.wema_average],
                name="Forecast",
            )

            chart_trace_mape = go.Scatter(
                x=[result.komoditas] * len(actual_values_parsed),
                y=[val for val in percentage_errors],
                mode="markers",
                name="MAPE Values",
                marker=dict(
                    color="blue",
                    size=8,
                    symbol="circle"
                ),
                hovertemplate="MAPE: %{text}%<extra></extra>",
                text=[str(val) for val in percentage_errors]
            )

            chart_trace_mape_forecast = go.Scatter(
                x=[result.komoditas, result.komoditas],
                y=[result.actual_values[-1], result.wema_average],
                mode="lines",
                name="MAPE Forecast",
                line=dict(
                    color="red",
                    width=1
                )
            )

            chart_trace_mape_lines = go.Scatter(
                x=[result.komoditas] * len(result.actual_values),
                y=[result.wema_average] * len(result.actual_values),
                mode="lines",
                name="MAPE Lines",
                line=dict(
                    color="red",
                    width=1,
                    dash="dash"
                )
            )

            chart_data.append(chart_trace_actual)
            chart_data.append(chart_trace_forecast)
            chart_data.append(chart_trace_mape)
            chart_data.append(chart_trace_mape_forecast)
            chart_data.append(chart_trace_mape_lines)

        # Konfigurasi layout grafik
        chart_layout = go.Layout(
            title="Grafik untuk Kelima Bahan Pokok",
            xaxis=dict(title="Komoditas"),
            yaxis=dict(title="Harga"),
        )

        chart_fig = go.Figure(data=chart_data, layout=chart_layout)
        chart_div = chart_fig.to_json()

        Result.objects.bulk_create(results)

        # Menampilkan hasil perhitungan dan grafik
        return render(
            request,
            "result.html",
            {"results": results, "span": span, "chart_div": chart_div},
        )

    return render(request, 'input.html')

31689.754611219105
20542.9000
40587.32351
14349.999
128350
[31650]
[20550]
[40600]
[14350]
[128350]

128350
14349.999
40587.32351
20542.9000
31689.754611219105
[128350]
[14350]
[40600]
[20550]
[31650]