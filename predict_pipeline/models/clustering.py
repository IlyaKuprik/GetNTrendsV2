from sklearn.cluster import KMeans, AgglomerativeClustering
import pandas as pd


class Agglomerative_Clustering:
    def __init__(self, text_pool, embeddings,
                 affinity='cosine', linkage='average',
                 distance_threshold=0.2, min_elements = 1, 
                 top_clusters = 10):
        """
            Класс для кластеризации эмбеддингов.
            На вход принмает информацию о новостях, эмбеддинги и количество кластеров.
            Если оно не задано, то задаётся эмпирически.
        """
        self.embeddings = embeddings
        self.text_pool = text_pool
        self.affinity = affinity # метрика cosine/euclid
        self.linkage = linkage # метод объединения классов single/average/complete
        self.distance_threshold = distance_threshold #порог ниже которого происходит объединение кластеров
        self.min_elements = min_elements
        self.top_clusters = top_clusters
        self.model = AgglomerativeClustering(n_clusters=None, affinity=self.affinity,
                                linkage = self.linkage,
                                distance_threshold = self.distance_threshold)

    def calculate_centroids(self, emb_lab_df):
        #return array: shape(num_clust, embeddings_len)
        #sorted from 0->num_clust-1
        unique_labels = sorted(emb_lab_df['label'].unique(), reverse=False)
        embeddings_size = emb_lab_df.loc[0,'embedding'].shape[0]
        centroids_map = {i:[] for i in unique_labels}
        for label in unique_labels:
            centroid = emb_lab_df[emb_lab_df['label'] == label]['embedding'].mean()
            centroids_map[label] = centroid
        return centroids_map

    def clustering(self):
        """
            Функция возвращает выполняющая поиск центроид кластеров.
            Выход: 
                data - датафрейм с информацией о новостях, в который добавлены
            метки кластеров и эмбеддинги,
                centoids_map - центроиды кластеров
        """
        print("Clustering data...")
        print(f'колонки в кластеризацию: {self.text_pool.columns}')
        self.model = self.model.fit(self.embeddings.to_list())
        model_labels = self.model.labels_
        print(f"Найдено {self.model.n_clusters_} кластеров")
        

        data = pd.DataFrame()
        data['text'] = self.text_pool['text']
        data['channel_id'] = self.text_pool['channel_id']
        data['category'] = self.text_pool['category']
        data['label'] = model_labels
        data['embedding'] = self.embeddings.to_list()

        counted_labels = data['label'].value_counts()
        filtered_labels = counted_labels[counted_labels >= self.min_elements].sort_values(ascending=False)
        filtered_labels = filtered_labels.iloc[:self.top_clusters].index
        data = data[data['label'].isin(filtered_labels)].reset_index(drop=True)
        print(f'Взято {len(filtered_labels)} кластеров из {self.top_clusters} запрошенных в которых минимум {self.min_elements} элементов')
        if not data.empty:
            centroids_map = self.calculate_centroids(data.loc[:, ['embedding', 'label']])
        else:
            centroids_map = {}
        print("Clustering done!")

        return data, centroids_map