from models.clustering import Agglomerative_Clustering
from models.embeddings import RuBertEmbedder
from models.features import get_digest, get_trends, get_insights

from datetime import datetime

import pandas as pd
import json

def calculate_features(text_pool: pd.DataFrame, testing=False) -> json:
    # костыль чтобы пайплайн не сломался, следующие 4 строчки нужно переписать нормально :) 
    text_pool = text_pool.dropna()
    text_pool['date'] = pd.to_datetime(text_pool['date'], format='%Y-%m-%d')
    text_pool['text'] = text_pool['content']
    text_pool['channel_id'] = text_pool['channel']
    text_pool['category'] = text_pool['channel']
    text_pool = text_pool[["date", "text", "channel_id", "category"]]

    if testing:
        text_pool = text_pool.head(100)

    # получение эмбеддингов из содержимого новостей
    embeddings_pool = RuBertEmbedder().encode_data(text_pool, data_column='text')

    # кластеризация эмбеддингов
    clustering_model = Agglomerative_Clustering(text_pool, embeddings_pool,
                                                affinity='cosine', linkage='complete',
                                                distance_threshold=0.275, min_elements = 3, 
                                                top_clusters = 40)
    clustering_data, centroids_map = clustering_model.clustering()

    digest = get_digest(clustering_data, centroids_map, top_clusters=5)  # дайджест
    insights = get_insights(clustering_data, centroids_map, top_for_cluster=5, max_news_len=300)  # инсайты

    return digest, insights

def format_response(digest: list, insights: list) -> json:
    formated_insights = []
    for insight in insights:
        elem = {}
        elem['insight'] = insight[0]
        elem['top_articles'] = insight[1]
        formated_insights.append(elem)

    formated_digest = []
    for cluster_id, data in enumerate(digest):
        elem = {}
        elem["cluster_id"] = cluster_id
        elem["top_cluster_articles"] = data[0]
        formated_digest.append(elem)

    result_json = {'digest': formated_digest, 'insights': formated_insights}

    return result_json

def save_response(response: json) -> None:
    curr_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    with open(f'data/history/result_{curr_datetime}.json', 'w') as f:
        json.dump(response, f)

    with open(f'data/latest.json', 'w') as f:
        json.dump(response, f)