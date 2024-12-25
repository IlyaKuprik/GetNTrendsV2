
import pandas as pd
from fastapi import FastAPI
from response_utils import calculate_features, format_response, save_response
import requests
from json import load


app = FastAPI()

@app.get("/get_actual_data")
async def get_actual_data():
    with open("data/latest.json", 'r') as file:
        actual_result = load(file)
    return actual_result

@app.get("/start_predict_pipeline")
def start_predict_pipeline(start_date: str = None, end_date: str = None):
    # получение данных из базы
    last_rows = requests.get("http://0.0.0.0:8001/get_all_rows").json() # идем в БД 
    news_df = pd.DataFrame(last_rows)

    digest, insights = calculate_features(news_df, testing=True)
    response = format_response(digest, insights)

    save_response(response)

    return response