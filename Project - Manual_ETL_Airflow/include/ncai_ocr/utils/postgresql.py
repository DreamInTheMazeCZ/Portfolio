from dotenv import load_dotenv
import psycopg2, os
import pandas as pd

load_dotenv()

class PostgreSQL:
    
    def __init__(self):
        self.__conn_info = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PW'),
            'host': os.getenv('DB_HOST'),
            'port':int(os.getenv('DB_PORT')),
        }

        
    def __connect_postgresql(self):
        '''
        DB Connection
        데이터베이스 연결
        '''
        # self.conn = psycopg2.connect(f'''
        #     dbname={self.__conn_info['dbname']} 
        #     user={self.__conn_info['user']} 
        #     password={self.__conn_info['password']}
        #     host={self.__conn_info['host']}
        # '''           
        # )
        self.conn = psycopg2.connect(**self.__conn_info)
        return self.conn

    
    def __close_db(self):
        '''
        DB Connection Close
        데이터베이스 연결 해제
        '''
        self.conn.close()
        return True

    
    def select_execute(self, query):
        '''
        SELECT 수행 메서드
        '''
        cur = self.__connect_postgresql().cursor()
        try:
            cur.execute(query)
            fetch = cur.fetchall()
            self.__close_db()
            return fetch
        except:
            self.conn.rollback()
            return False
        finally:
            cur.close()
            self.__close_db()

    
    def query_execute(self, query):
        '''
        INSERT, UPDATE 수행 메서드
        '''
        cur = self.__connect_postgresql().cursor()
        try:
            cur.execute(query)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            # self.logger.exception(f'EXECUTE ERROR - {e}')
            return False
        finally:
            cur.close()
            self.__close_db()


    def executemany_query(self, query, data):
        '''
        executemany 기능
        '''
        cur = self.__connect_postgresql().cursor()
        try:
            cur.executemany(query, data)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            # self.logger.exception(f'EXECUTEMANY ERROR - {e}')
            print(e)
            return False
        finally:
            cur.close()
            self.__close_db()