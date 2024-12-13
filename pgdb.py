# A class for working with a database

import psycopg2
from psycopg2 import extensions
from dataclasses import dataclass

from config_py import DBConnectionSettings

# Type's hints
Row = tuple
Rows = tuple[Row]
ConnectionType = psycopg2.extensions.connection

@dataclass(slots=True, frozen=True)
class DBQueryResult :
    is_successful: bool    # this is the success flag
    value: tuple | int | None    # received data


class Database :
    def __init__(self, db_connect_set: DBConnectionSettings) :
        ''' Constructor '''
        self.db_connect_set = db_connect_set
        try :
            self.connect: ConnectionType = psycopg2.connect(
                **db_connect_set.model_dump()
            )
            print("Data base Successfully connected.")
        except Exception as e :
            print(f"An error occurred while connecting: {e}")

    def run_query(self, query: str, params: tuple = (), several: bool = False) -> DBQueryResult :
        ''' Main method '''
        try :
            with self.connect:
                with self.connect.cursor() as cursor :
                    if several :
                        cursor.executemany(query, params)
                    else :
                        cursor.execute(query, params)

                    # We return the data if the request suggested it
                    if cursor.description :
                        return DBQueryResult(True, cursor.fetchall())

                    # In other cases, we return the number of affected rows
                    return DBQueryResult(True, cursor.rowcount)

        except Exception as e :
            print(f"An error occurred while executing the request: {e}")
            return DBQueryResult(False, None)


    def read_rows(self,
                  table_name: str,
                  columns_statement: str = '*',
                  condition_statement='',
                  limit: int = 0) -> DBQueryResult :
        if table_name :
            query = f'SELECT {columns_statement} FROM {table_name}'
            if condition_statement :
                query += f' WHERE {condition_statement}'
            if limit > 0 :
                query += f' LIMIT {limit}'
            return self.run_query(query)
        return DBQueryResult(False, None)


    def search_table(self, table_name: str) -> bool :
        ''' Table search '''
        if table_name :
            query = (f'SELECT table_name FROM information_schema.tables '
                    f'WHERE table_schema=\'public\' AND table_type=\'BASE TABLE\' '
                    f'AND table_name = \'{table_name}\'')
            res = self.run_query(query)
            if res.is_successful and len(res.value) != 0 :
                return True
        return False


    def create_table(self,
                     table_name: str,
                     columns_statement: str,
                     overwrite: bool = False) -> DBQueryResult :
        ''' Creating a new table '''
        if table_name and columns_statement :
            if self.search_table(table_name) :
                if overwrite :
                    query = f'DROP TABLE {table_name}'
                    if not self.run_query(query).is_successful :
                        # print(f'The already existing table {table_name} has not been deleted.')
                        return DBQueryResult(False, None)
                    # print(f'The already existing table {table_name} has been deleted.')
                else:
                    # print(f'Error, table {table_name} is already there.')
                    return DBQueryResult(False, None)
            query = f'CREATE TABLE {table_name} ({columns_statement})'
            return self.run_query(query)
        else :
            return DBQueryResult(False, None)


    def insert_row(self, table_name: str, values: Row) -> DBQueryResult:
        ''' Inserting a single row into a table. '''
        if table_name and len(values) > 0 :
            placeholders = ', '.join(['%s'] * len(values))
            query = f"INSERT INTO {table_name} VALUES ({placeholders})"
            return self.run_query(query, params=values)
        return DBQueryResult(False, 0)


    def insert_rows(self, table_name: str, values: Rows) -> DBQueryResult:
        ''' Inserting multiple rows into a table. '''
        if table_name and len(values) > 0 and len(values[0]) > 0 :
            placeholders = ', '.join(['%s'] * len(values[0]))
            query = f"INSERT INTO {table_name} VALUES ({placeholders})"
            return self.run_query(query, params=values, several=True)
        return DBQueryResult(False, 0)


    def update_data(self, table_name, set_values, condition) :
        """Обновление данных в таблице."""
        query = f"UPDATE {table_name} SET {set_values} WHERE {condition}"
        self.execute_query(query)
        self.commit()


    def delete_rows(self, table_name, condition) :
        """Удаление строк из таблицы."""
        query = f"DELETE FROM {table_name} WHERE {condition}"
        self.execute_query(query)
        self.commit()


    def count_rows(self, table_name):
        """Получение количества строк в таблице."""
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.execute_query(query)
        return result[0][0]


    def close_connection(self) :
        ''' Closing the database connection '''
        try :
            self.connect.close()
            print('The connection to the database is closed.')
        except Exception as e :
            print(f"An error occurred when closing the connection: {e}")
