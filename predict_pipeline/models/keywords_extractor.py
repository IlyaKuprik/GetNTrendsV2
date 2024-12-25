import torch
from itertools import groupby
import numpy as np
from transformers import T5ForConditionalGeneration, T5Tokenizer


class KeyWordsExtractor:

    def __init__(self, model_name="0x7194633/keyt5-large"):
        self.model_name = model_name

        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)
        if torch.cuda.is_available():
            self.model.cuda()

        self.device = self.model.device

    def generate(self, text, **kwargs):
        """
        Производим генерацию keywords
        """

        inputs = self.tokenizer(text, return_tensors='pt').to(self.device)

        with torch.no_grad():
            hypotheses = self.model.generate(**inputs, num_beams=5, **kwargs)

        s = self.tokenizer.decode(hypotheses[0], skip_special_tokens=True)
        s = s.replace('; ', ';').replace(' ;', ';').lower().split(';')[:-1]
        gamma = 1
        s = [el for el, _ in groupby(s)]
        weights = [gamma ** i for i in range(len(s))]

        return s, weights

    def get_keywords(self, set_of_articles, **kwargs):
        """
        Получаем отсортированные по частоте сгенерированные ключевые фразы из набора статей

        [(key_1, weight_1), (key_2, weight_2), ....]
        """

        keys_weights = []
        len_set = len(set_of_articles)

        for i in range(len_set):
            text = set_of_articles[i]
            keys_weights.append(self.generate(text, **kwargs))

        return sort_and_remove_repeat(keys_weights)

    def get_trends(self, set_of_articles, n=5, threshold=0.95, **kwargs):
        """
        Получаем n трендовых ключевых слов
        """

        keys = self.get_keywords(set_of_articles, **kwargs)

        keys, _ = self.cos_simularity(keys, threshold=threshold)

        return keys[:n]

    def get_embed(self, text):
        t = self.tokenizer(text.replace('\n', ''), padding=True, truncation=True, return_tensors='pt').to(self.device)
        with torch.no_grad():
            model_output = self.model.encoder(input_ids=t.input_ids, attention_mask=t.attention_mask, return_dict=True)
        embeddings = model_output.last_hidden_state[:, 0, :]
        embeddings = torch.nn.functional.normalize(embeddings)
        return embeddings[0].cpu()

    def cos_simularity(self, keys_weights, threshold=0.95):
        """
        Считаем косинусную схожесть, возвращаем отсортированный по частоте список
        объединённый ключей таблицу взаимной схожести
        """

        new_keys_weights = []

        cos_sim = np.ones((len(keys_weights), len(keys_weights)))

        cos = torch.nn.CosineSimilarity(dim=1)

        for i in range(len(keys_weights)):
            sim_keys = [keys_weights[i][0]]
            sim_weight = keys_weights[i][1]
            embed_i = torch.unsqueeze(self.get_embed(keys_weights[i][0]), 0)
            for j in range(i + 1, len(keys_weights)):
                embed_2 = torch.unsqueeze(self.get_embed(keys_weights[j][0]), 0)

                cos_sim[i][j] = cos(embed_i, embed_2).numpy()[0]
                cos_sim[j][i] = cos_sim[i][j]

                if cos_sim[i][j] > threshold:
                    sim_keys.append((keys_weights[j][0]))
                    sim_weight += keys_weights[j][1]

            new_keys_weights.append((sim_keys, [sim_weight]))
        return sorted(new_keys_weights, key=lambda tup: tup[1], reverse=True), cos_sim


def sort_and_remove_repeat(keys_weights):
    """
    Убираем повторения
    Сортируем по второму аргументу массив вида [([x1], [y1]), ([x2], [y2]), ...],
    где
    * y2 - это частота
    * x1 - это ключевое слово
    """
    dict_keys = {}
    set_stop_words = {'анализ и проектирование систем', 'промышленное программирование', 'читальный зал',
                      'разработка веб-сайтов', 'программирование микроконтроллеров',
                      'системное программирование', 'ненормальное программирование',
                      'мобильная разработка', 'разработка мобильных приложений', 'будущее здесь',
                      'научно-популярное', 'платежи в интернет', 'платежи с мобильного', 'разработка игр',
                      'монетизация игр', 'дизайн игр', 'информационная безопасность', 'фейковые новости'}

    for i in range(len(keys_weights)):
        for j in range(len(keys_weights[i][0])):
            if keys_weights[i][0][j].lower() in set_stop_words:
                continue
            elif not (keys_weights[i][0][j] in dict_keys):
                dict_keys[keys_weights[i][0][j]] = keys_weights[i][1][j]
            else:
                dict_keys[keys_weights[i][0][j]] += keys_weights[i][1][j]

    dict_zip = list(zip(dict_keys.keys(), dict_keys.values()))

    return sorted(dict_zip, key=lambda tup: tup[1], reverse=True)
