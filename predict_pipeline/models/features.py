import numpy as np
import torch
from tqdm import tqdm
from sklearn.metrics.pairwise import euclidean_distances, pairwise_distances
from transformers import T5ForConditionalGeneration, T5Tokenizer

from models.keywords_extractor import KeyWordsExtractor


def get_top_articles(data, centroids_map, top_k=5, text_col='text', metric='cosine'):
    """
        Функция выделяет ближайших к центру top_k новостей для каждого кластера.
        Вход:
            data - данные о новостях с текстами и эмбеддингами,
            
    """
    top_texts_list = []

    for label, cluster_center in centroids_map.items():
        cluster = data[data['label'] == label]
        embeddings = list(cluster['embedding'])
        texts = cluster[text_col].values.tolist()

        distances = [pairwise_distances(cluster_center.reshape(1, -1), e.reshape(1, -1), metric=metric)[0][0] for e in embeddings]
        scores = list(zip(texts, distances))
        top_ = sorted(scores, key=lambda x: x[1])[:top_k]
        top_texts = list(zip(*top_))[0]
        top_texts_list.append(top_texts)

    return top_texts_list


def summarize(tokenizer, model, text, n_words=None, compression=None, max_length=1000, num_beams=3, do_sample=False,
              repetition_penalty=10.0):
    if n_words:
        text = '[{}] '.format(n_words) + text
    elif compression:
        text = '[{0:.1g}] '.format(compression) + text
    x = tokenizer(text, return_tensors='pt', padding=True)

    with torch.inference_mode():
        out = model.generate(
            **x,
            max_length=max_length, num_beams=num_beams,
            do_sample=do_sample, repetition_penalty=repetition_penalty
        )
    return tokenizer.decode(out[0], skip_special_tokens=True)


def get_digest(data, centroids_map, top_clusters=5):
    print("Getting digest...")
    top_label = data['label'].value_counts()[:top_clusters].index.to_list()
    local_centroids = {label: centroids_map[label] for label in top_label}

    return get_top_articles(data, local_centroids, top_k=3, text_col=['text', 'channel_id', 'category'])


def get_trends(data, centroids_map, top_for_cluster=10, max_news_len=200, text_col='title_text'):
    words_extractor = KeyWordsExtractor()

    top_articles_for_clusters = get_top_articles(data, centroids_map, top_k=top_for_cluster, text_col=text_col)

    trends_list = []
    pbar = tqdm(total=len(top_articles_for_clusters))
    pbar.set_description("Getting trends...")
    for top_articles in top_articles_for_clusters:
        top_articles = [' '.join(row.split(' ')[:max_news_len]) for row in top_articles]
        
        current_trends = words_extractor.get_trends(top_articles, threshold=0.95, top_p=1.0, max_length=256, min_length=5)
        current_trends = [x[0][0] for x in current_trends]

        trends_list.append((current_trends, top_articles))
        pbar.update(1)

    pbar.close()

    return trends_list


def get_insights(data, centroids_map, top_for_cluster=10, max_news_len=200, text_col='text'):
    t5_model = T5ForConditionalGeneration.from_pretrained('cointegrated/rut5-base-absum')
    t5_tokenizer = T5Tokenizer.from_pretrained('cointegrated/rut5-base-absum')

    top_articles_for_clusters = get_top_articles(data, centroids_map, top_k=top_for_cluster, text_col=text_col)

    insights_list = []
    pbar = tqdm(total=len(top_articles_for_clusters))
    pbar.set_description("Getting insights...")
    for top_articles in top_articles_for_clusters:

        top_articles_concat = [' '.join(row.split(' ')[:max_news_len]) for row in top_articles]
        insights_list.append((summarize(t5_tokenizer, t5_model, ' '.join(top_articles_concat)), top_articles))
        pbar.update(1)

    pbar.close()
    print(insights_list)
    return insights_list
