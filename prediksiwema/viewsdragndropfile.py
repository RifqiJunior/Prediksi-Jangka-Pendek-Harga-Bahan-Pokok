# views.py yang bisa drag n drop file excel
from django.shortcuts import render
from .models import Result
import pandas as pd
import numpy as np
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
        
        komoditas = ['Daging Ayam', 'Daging Sapi', 'Telur Ayam', 'Minyak Goreng', 'Gula Pasir']
        results = []
        
        for i, kom in enumerate(komoditas, 1):
            wema = ExponentialWeightedMovingAverage(int(span) + 1)
            values = df[df['Komoditas()'] == kom].iloc[:, 1:].values.flatten()
            values = pd.to_numeric(values, errors='coerce')
            values = [value for value in values if not np.isnan(value)]
            
            for value in values:
                wema.update([value])
            
            actual_values = df.loc[df['Komoditas()'] == kom].iloc[:, -1:].values.flatten()
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
                actual_values=actual_values,
                mape_percentage=mape_percentage
            )
            
            results.append(result)
        
        Result.objects.bulk_create(results)
        return render(request, 'result.html', {'results': results})
    
    return render(request, 'input.html')
