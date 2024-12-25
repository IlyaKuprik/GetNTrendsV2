from transformers import AutoTokenizer, AutoModel
import torch


class RuBertEmbedder:

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("cointegrated/rubert-tiny2")
        self.model = AutoModel.from_pretrained("cointegrated/rubert-tiny2")

        if torch.cuda.is_available():
            self.model.cuda()

        self.device = self.model.device

    def embed_bert_cls(self, text):
        """Получение эмбеддингов из текста"""
        t = self.tokenizer(text.replace('\n', ''), padding=True, truncation=True, return_tensors='pt')
        with torch.no_grad():
            model_output = self.model(**{k: v.to(self.device) for k, v in t.items()})
        embeddings = model_output.last_hidden_state[:, 0, :]
        embeddings = torch.nn.functional.normalize(embeddings)
        return embeddings[0].cpu().numpy()

    def encode_data(self, text_pool, data_column='text'):
        print("Encoding data...")
        """
            Вход:
                content - содержимое новости
                date - дата публикации
            Выход:
                embeddings_pool- list с эмбеддингами новостей
        """
        embeddings_pool = text_pool.apply(
            lambda x: self.embed_bert_cls(x[data_column]), axis=1
        )
        print("Encoding done!")
        return embeddings_pool
