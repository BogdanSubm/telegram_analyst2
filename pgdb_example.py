# Example of working with the <Database> class

from pgdb import Database, Rows
from config_py import settings
from faker import Faker


def generate_fake_data(start: int, count: int) -> Rows :
    ''' Generating fake data for the demo function <main> '''
    # fake = Faker('ru_RU')
    fake = Faker('en_US')
    fake_rows = ((str(_), fake.company()[0:30]) for _ in range(start, start+count+1))
    return fake_rows


def main() -> bool :
    ''' Demonstration of methods of the <Database> class '''

    # Creating an instance of a Database class
    #   ... opening the connection inside
    db = Database(settings.database_connection)
    if not db.is_connected : return False

    # Reading data from an existing table
    res = db.read_rows(table_name='channel',
                       condition_statement='name >= \'Data\'',
                       limit=2
                       )
    if res.is_successful : print(res.value)

    # Creating a simple table (with overwriting if already available):
    #   name: 'new_table'
    #   field 1: 'post_id' (unique values)
    #   field 2: 'post_name'
    #
    res = db.create_table(table_name='new_table',
            columns_statement='post_id VARCHAR(10) UNIQUE, post_name VARCHAR(30)',
                          overwrite=True
                          )
    if not res.is_successful:
        return False

    # Generating a fake data (25 lines)
    data = tuple(generate_fake_data(1, 25))

    # Inserting data into a table
    res = db.insert_rows(table_name='new_table', values=data)
    if not res.is_successful : return False

    # Changing the data in the table for multiple rows
    db.update_data(table_name='new_table',
                   set_statement='post_name = \'TEST1\'',
          condition_statement='post_id in (\'10\', \'11\', \'12\', \'13\', \'15\')'
                   )

    # Other changing the data in the table for multiple rows
    db.update_data(table_name='new_table',
                   set_statement='post_name = \'TEST2\'',
                   condition_statement='post_id in (\'20\', \'21\', \'22\')'
                   )

    # Inserting data into a table using the <run_query> method
    data = ('25', 'REPLACEMENT DATA')
    insert_query = '''
                INSERT INTO new_table (post_id, post_name) VALUES (%s, %s)
                ON CONFLICT (post_id) DO UPDATE
                SET post_name = EXCLUDED.post_name;
    '''
    res = db.run_query(query=insert_query, params=data)

    # Counting the total number of rows in the table
    res = db.count_rows('new_table')
    print(f'The total number of rows in the table: {res.value}')

    # Deleting few rows from a table by condition
    res = db.delete_rows('new_table', 'post_name = \'TEST1\'')
    print(f'{res.value} lines have been deleted...')

    # Counting the total number of rows in the table
    res = db.count_rows('new_table')
    print(f'The total number of rows in the table: {res.value}')

    # Shutting down the connection
    db.close_connection()

    return True


if __name__ == '__main__':

    if main():
        print('done... :) !')
    else:
        print('damn... :(')
