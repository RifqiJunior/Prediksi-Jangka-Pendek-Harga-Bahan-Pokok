from django.shortcuts import render
import plotly.graph_objects as go
from .models import Result
import plotly

def result_view(request):
    # Mengambil data dari database
    results = Result.objects.all()

    # Menyiapkan data untuk grafik
    x = [result.komoditas for result in results]
    actual_values = [result.actual_values for result in results]
    wema_average = [result.wema_average for result in results]

    # Membuat grafik garis
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=actual_values, mode='lines', name='Actual'))
    fig.add_trace(go.Scatter(x=x, y=wema_average, mode='lines', name='Forecast'))

    # Menyimpan grafik dalam bentuk HTML
    plot_div = plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')


    # Menampilkan template dan mengirimkan data grafik ke template
    return render(request, 'result.html', {'chart_div': graph_div})
