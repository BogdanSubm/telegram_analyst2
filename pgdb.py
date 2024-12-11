# A class for working with a database

import psycopg2
from psycopg2 import extensions

Connection_type = psycopg2.extensions.connection
Query_return_type = tuple[bool, tuple | int | None]


class Database :
    def __init__(self, host, port, dbname, user, password) :
        ''' Constructor '''
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password

        try :
            self.connect: Connection_type = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
            # self.cursor = self.connect.cursor()
            print("Successfully connected...")
        except Exception as e :
            print(f"An error occurred while connecting: {e}")

    def _execute(self, query: str, params: tuple = (), many: bool = False) -> Query_return_type :
        ''' Main method '''
        try :
            with self.connect:
                with self.connect.cursor() as cursor :
                    if many :
                        cursor.executemany(query, params)
                    else :
                        cursor.execute(query, params)

                    # We return the data if the request suggested it
                    if cursor.description:
                        return True, cursor.fetchall()

                    # In other cases, we return the number of affected rows
                    return True, cursor.rowcount

        except Exception as e :
            print(f"An error occurred while executing the request: {e}")
            return False, None


    def query(self, query: str, params: tuple = (), many: bool = False) -> Query_return_type :
        ''' А simple query '''
        return self._execute(query, params, many)


    def read_rows(self, table_name: str, query: str, columns: list = ['*'], ) -> tuple :
        query = f'SELECT {", ".join(columns)} FROM {table_name}'
        return

    #
    # def read_many(self, query: str, params: tuple = ()) -> tuple:
    #
    #     self._execute(query, params=(), many=False)
    #     try :
    #         self.cursor.execute(query, params)
    #         # We return the data if the request suggested it
    #         if self.cursor.description :
    #             return self.cursor.fetchall()
    #
    #         # In other cases, we return the number of affected rows
    #         return self.cursor.rowcount
    #     except Exception as e :
    #         print(f"An error occurred while executing the request: {e}")
    #
    # def commit(self) :
    #     """Фиксация изменений в базе данных"""
    #     try :
    #         self.connect.commit()
    #         print("Изменения зафиксированы.")
    #     except Exception as e :
    #         print(f"Произошла ошибка при фиксации изменений: {e}")
    #
    # def create_table(self, table_name, columns) :
    #     """Создание новой таблицы."""
    #     query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
    #     self.execute_query(query)
    #     self.commit()
    #
    # def insert_row(self, table_name, values) :
    #     """Вставка одной строки в таблицу."""
    #     placeholders = ', '.join(['%s'] * len(values))
    #     query = f"INSERT INTO {table_name} VALUES ({placeholders})"
    #     self.execute_query(query, values)
    #     self.commit()
    #
    # def update_data(self, table_name, set_values, condition) :
    #     """Обновление данных в таблице."""
    #     query = f"UPDATE {table_name} SET {set_values} WHERE {condition}"
    #     self.execute_query(query)
    #     self.commit()
    #
    # def delete_rows(self, table_name, condition) :
    #     """Удаление строк из таблицы."""
    #     query = f"DELETE FROM {table_name} WHERE {condition}"
    #     self.execute_query(query)
    #     self.commit()
    #
    #
    #
    # def count_rows(self, table_name):
    #     """Получение количества строк в таблице."""
    #     query = f"SELECT COUNT(*) FROM {table_name}"
    #     result = self.execute_query(query)
    #     return result[0][0]
    #
    # def select_by_condition(self, table_name, columns='*', condition=''):
    #     """Выборка данных из таблицы по условию."""
    #     query = f"SELECT {columns} FROM {table_name}"
    #     if condition:
    #         query += f" WHERE {condition}"
    #     result = self.execute_query(query)
    #     return result
    #
    # def generate_report(self, table_name, column, aggregation_function='SUM'):
    #     """Генерация отчета по указанному столбцу."""
    #     query = f"SELECT {aggregation_function}({column}) FROM {table_name}"
    #     result = self.execute_query(query)
    #     return result[0][0]
    #

    def close_connection(self) :
        ''' Closing the database connection '''
        try :
            self.connect.close()
            print('The connection to the database is closed.')
        except Exception as e :
            print(f"An error occurred when closing the connection: {e}")
