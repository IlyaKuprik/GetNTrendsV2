import sqlite3 as sql

def make_json_response(rows):
    return [dict(zip(["id", "channel", "date", "content"], row)) for row in rows]

class SQLite3DB:
    def __init__(self, db_path):
        self.connection = sql.connect(db_path, check_same_thread=False)

        self.init_tables()

    def init_tables(self):
        with self.connection:
            cur = self.connection.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS `LastParseDate` (
                        channel_name TEXT NOT NULL PRIMARY KEY,
                        last_parsed_post_date TEXT
                    );
                """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS `ParsedData` (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        channel_name TEXT,
                        publication_date TEXT,
                        publication_content TEXT
                    );
                """)
            
            cur.execute("""
                DELETE FROM `ParsedData`;
                """)
            
            self.connection.commit()


    def add_message(
            self, 
            channel_name, 
            publication_date, 
            publication_content
        ):

        insert_query = \
        """INSERT INTO `ParsedData` (
                channel_name, 
                publication_date, 
                publication_content
                ) VALUES (?, ?, ?);"""
        
        
        with self.connection:
            cur = self.connection.cursor()
            cur.execute(insert_query,
                (
                    channel_name, 
                    publication_date, 
                    publication_content
                )
            )

    def select_all_data(self, table_name):
        select_all_rows = f"SELECT * FROM `{table_name}`"
        with self.connection:
            cur = self.connection.cursor()
            cur.execute(select_all_rows)
            rows = cur.fetchall()
            return make_json_response(rows)
        
    def select_last_n_rows(self, table_name, n=10):
        select_all_rows = f"SELECT * FROM `{table_name}` ORDER BY publication_date DESC LIMIT {n}"
        with self.connection:
            cur = self.connection.cursor()
            cur.execute(select_all_rows)
            rows = cur.fetchall()
            return make_json_response(rows)
        
    def update_last_date(self, channel_name):
        """
            обновляем дату последнего спаршенного поста в LastParseDate на основе ParsedData
        """

        update_query = f""" \
            INSERT or REPLACE into LastParseDate (channel_name, last_parsed_post_date) VALUES
            ('{channel_name}', (SELECT MAX(publication_date) FROM ParsedData WHERE channel_name == '{channel_name}'))
        """

        with self.connection:
            cur = self.connection.cursor()
            cur.execute(update_query)

    def __del__(self):
        self.connection.close()