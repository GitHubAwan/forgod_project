# database.py
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool  # 显式导入 QueuePool
import configparser

# 实例化 configparser
config=configparser.ConfigParser()
# 读取 config.ini 文件
config.read('config.ini')

# 从 config.ini 的 [DatabaseConfig] 部分获取数据库配置
DB_CONFIG={
    'host': config.get('DatabaseConfig', 'host'),
    'user': config.get('DatabaseConfig', 'user'),
    'password': config.get('DatabaseConfig', 'password'),
    'db': config.get('DatabaseConfig', 'db')
}


class Database:
    def __init__(self, host, user, password, db):
        # 构建数据库连接字符串
        # 格式：'mysql+pymysql://user:password@host/db_name?charset=utf8mb4'
        # pymysql 是 SQLAlchemy 连接 MySQL 的推荐驱动
        self.database_url=f"mysql+pymysql://{user}:{password}@{host}/{db}?charset=utf8mb4"

        # 使用 create_engine 创建数据库引擎，它自带连接池
        self.engine=create_engine(
            self.database_url,
            poolclass=QueuePool,  # 明确指定使用 QueuePool
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,  # seconds
            pool_recycle=3600,  # seconds (1 hour)
            echo=False  # 设置为 True 可以打印所有执行的 SQL，方便调试
        )
        print("SQLAlchemy engine with connection pool initialized.")

    def connect(self):
        try:
            return self.engine.connect()  # 从连接池获取连接
        except sqlalchemy.exc.SQLAlchemyError as e:
            print(f"Error getting connection from SQLAlchemy engine: {e}")
            return None

    def close(self):
        # SQLAlchemy 连接池由 engine 自动管理，这里的方法留空
        pass

    def fetch_all(self, query, params=None):
        conn=None
        try:
            conn=self.connect()
            if not conn: return None
            # 使用 text() 明确标记这是一个文本 SQL 语句，防止 SQL 注入
            # params 应该是一个字典，例如 {'id': 1}
            result=conn.execute(text(query), params)
            # 将结果转换为字典列表
            return [dict(row) for row in result.mappings().all()]
        except sqlalchemy.exc.SQLAlchemyError as e:
            print(f"Error executing fetch_all query: {e}")
            return None
        finally:
            if conn:
                conn.close()  # 连接返回连接池

    def fetch_one(self, query, params=None):
        conn=None
        try:
            conn=self.connect()
            if not conn: return None
            result=conn.execute(text(query), params)
            row=result.mappings().fetchone()
            return dict(row) if row else None
        except sqlalchemy.exc.SQLAlchemyError as e:
            print(f"Error executing fetch_one query: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def execute_query(self, query, params=None):
        conn=None
        try:
            conn=self.connect()
            if not conn: return False
            conn.execute(text(query), params)
            conn.commit()  # SQLAlchemy 自动管理事务，这里需要显式提交
            return True
        except sqlalchemy.exc.SQLAlchemyError as e:
            print(f"Error executing execute_query: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def executemany_query(self, query, param_list):
        conn=None
        try:
            conn=self.connect()
            if not conn: return False
            # 对于 executemany，param_list 应该是一个字典的列表
            conn.execute(text(query), param_list)
            conn.commit()
            return True
        except sqlalchemy.exc.SQLAlchemyError as e:
            print(f"Error executing executemany_query: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()


# DB_CONFIG 保持不变，以便 app.py 可以导入
DB_CONFIG=DB_CONFIG