import sqlite3
from typing import Optional, Dict, List, Any
from datetime import datetime

class SQLiteManager:
    def __init__(self, db_path: str = ":memory:"):
        """初始化数据库连接
        :param db_path: 数据库文件路径，默认内存数据库
        """
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        print(f"Connected to database: {db_path}")
        self.initialize_tables()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭连接"""
        self.close()

    def initialize_tables(self):
        """初始化所有表"""
        self.create_table("users", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL UNIQUE",
            "status": "TEXT NOT NULL DEFAULT '未激活'",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        })
        self.create_table("short_memory", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL",
            "content": "TEXT NOT NULL",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        })
        self.create_table("day_memory", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL",
            "content": "TEXT NOT NULL",
            "date": "DATE"
        })
        self.create_table("week_memory", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL",
            "content": "TEXT NOT NULL",
            "streamline": "TEXT NOT NULL",
            "date": "TEXT NOT NULL"
        })
        self.create_table("month_memory", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL",
            "content": "TEXT NOT NULL",
            "streamline": "TEXT NOT NULL",
            "date": "TEXT NOT NULL"
        })
        self.create_table("year_memory", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL",
            "content": "TEXT NOT NULL",
            "streamline": "TEXT NOT NULL",
            "date": "INTEGER"
        })
        self.create_table("long_memory", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL",
            "content": "TEXT NOT NULL",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        })

    def create_table(self, table_name: str, columns: Dict[str, str]):
        """创建数据表
        :param table_name: 表名称
        :param columns: 字段字典 {列名: 数据类型}
        """
        columns_def = ", ".join([f"{k} {v}" for k, v in columns.items()])
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})"
        self.execute(sql)
        print(f"Table '{table_name}' created/verified")

    def execute(self, sql: str, params: tuple = (), commit: bool = True) -> Optional[List[tuple]]:
        """执行SQL语句
        :param sql: SQL语句
        :param params: 参数元组
        :param commit: 是否自动提交
        :return: 查询结果集（如果有）
        """
        try:
            self.cursor.execute(sql, params)
            if sql.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            if commit:
                self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Database error: {e}")

    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """插入数据
        :param table_name: 表名称
        :param data: 数据字典 {列名: 值}
        :return: 插入行的rowid
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.execute(sql, tuple(data.values()))
        return self.cursor.lastrowid

    def update(self, table_name: str, data: Dict[str, Any], condition: Dict[str, Any]) -> int:
        """更新数据
        :param table_name: 表名称
        :param data: 更新数据字典 {列名: 新值}
        :param condition: 条件字典 {列名: 值}
        :return: 受影响的行数
        """
        set_clause = ", ".join([f"{k} = ?" for k in data])
        where_clause = " AND ".join([f"{k} = ?" for k in condition]) if condition else "1=1"
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        params = tuple(data.values()) + tuple(condition.values())
        self.execute(sql, params)
        return self.cursor.rowcount

    def delete(self, table_name: str, condition: Dict[str, Any]) -> int:
        """删除数据
        :param table_name: 表名称
        :param condition: 条件字典 {列名: 值}
        :return: 受影响的行数
        """
        where_clause = " AND ".join([f"{k} = ?" for k in condition]) if condition else "1=1"
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        self.execute(sql, tuple(condition.values()))
        return self.cursor.rowcount

    def fetch_all(self, table_name: str, condition: Dict[str, Any] = None) -> List[tuple]:
        """查询数据
        :param table_name: 表名称
        :param condition: 条件字典 {列名: 值}
        :return: 结果列表
        """
        where_clause = " AND ".join([f"{k} = ?" for k in condition]) if condition else "1=1"
        sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
        params = tuple(condition.values()) if condition else ()
        return self.execute(sql, params)

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        print("Database connection closed")

# 使用示例
if __name__ == "__main__":
    # 初始化数据库（内存数据库）
    with SQLiteManager("loom.db") as db:
        # 插入用户信息
        user_id = db.insert("users", {
            "user_id": 1,
            "status": "用户"
        })
        print(f"Inserted user ID: {user_id}")

        # 查询用户信息
        all_users = db.fetch_all("users")
        print("All users:", all_users)

        # 插入short_memory数据，手动指定时间戳
        timestamp = datetime.now().isoformat()
        short_memory_id = db.insert("short_memory", {
            "user_id": 1,
            "content": "User performed action A",
            "timestamp": timestamp
        })
        print(f"Inserted short memory ID: {short_memory_id}")

        # 从short_memory表中查询数据
        all_short_memory = db.fetch_all("short_memory")
        print("All short memory entries:", all_short_memory)

        # 插入day_memory数据
        day_memory_id = db.insert("day_memory", {
            "user_id": 1,
            "content": "Summary of user actions for the day",
            "date": "2023-10-01"
        })
        print(f"Inserted day memory ID: {day_memory_id}")

        # 从day_memory表中查询数据
        all_day_memory = db.fetch_all("day_memory")
        print("All day memory entries:", all_day_memory)

        # 插入week_memory数据
        week_memory_id = db.insert("week_memory", {
            "user_id": 1,
            "content": "Summary of user actions for the week",
            "week": "2023-40"
        })
        print(f"Inserted week memory ID: {week_memory_id}")

        # 从week_memory表中查询数据
        all_week_memory = db.fetch_all("week_memory")
        print("All week memory entries:", all_week_memory)

        # 插入year_memory数据
        year_memory_id = db.insert("year_memory", {
            "user_id": 1,
            "content": "Summary of user actions for the year",
            "year": 2023
        })
        print(f"Inserted year memory ID: {year_memory_id}")

        # 从year_memory表中查询数据
        all_year_memory = db.fetch_all("year_memory")
        print("All year memory entries:", all_year_memory)

        # 插入long_memory数据，手动指定时间戳
        long_memory_timestamp = datetime.now().isoformat()
        long_memory_id = db.insert("long_memory", {
            "user_id": 1,
            "content": "Long-term summary of user actions",
            "timestamp": long_memory_timestamp
        })
        print(f"Inserted long memory ID: {long_memory_id}")

        # 从long_memory表中查询数据
        all_long_memory = db.fetch_all("long_memory")
        print("All long memory entries:", all_long_memory)
