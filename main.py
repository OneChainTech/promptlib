import pandas as pd
import sqlite3

rootpath = '/Users/zhenghong/Documents/work/aigc/'


# 打开数据库连接
conn = sqlite3.connect(rootpath + 'prompt1.db')
cursor = conn.cursor()

# 创建表结构
create_table_sql = """
CREATE TABLE IF NOT EXISTS words (
    分类 TEXT,
    中文 TEXT,
    英文 TEXT
);
"""
cursor.execute(create_table_sql)
conn.commit()

# 加载Excel文件
file_path = rootpath + 'prompt.xlsx'
xls = pd.ExcelFile(file_path)

# 迭代每个工作表并导入数据
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    # 确保列名匹配，移除不需要的列
    if {'分类', '中文', '英文'}.issubset(df.columns):
        df = df[['分类', '中文', '英文']]
        # 导入数据到SQLite
        df.to_sql('words', conn, if_exists='append', index=False)

# 关闭数据库连接
conn.close()

"所有工作表的数据已导入到数据库。"


from fastapi import FastAPI, HTTPException, Query
import sqlite3
from typing import List
from pydantic import BaseModel

app = FastAPI()

# 定义模型
class WordItem(BaseModel):
    分类: str
    中文: str
    英文: str

# 连接数据库的函数
def get_db_connection():
    conn = sqlite3.connect(rootpath + 'prompt1.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/promptlib/items", response_model=List[WordItem])
async def read_items():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM words")
    items = cursor.fetchall()
    conn.close()
    return [dict(item) for item in items]

@app.get("/promptlib/items/{category}", response_model=List[WordItem])
async def read_items_by_category(category: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM words WHERE 分类 = ?", (category,))
    items = cursor.fetchall()
    conn.close()
    if items:
        return [dict(item) for item in items]
    else:
        raise HTTPException(status_code=404, detail="Category not found")

@app.get("/promptlib/search", response_model=List[WordItem])
async def search_items(q: str = Query(None, min_length=1)):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"%{q}%"
    cursor.execute("SELECT * FROM words WHERE 中文 LIKE ?", (query,))
    items = cursor.fetchall()
    conn.close()
    if items:
        return [dict(item) for item in items]
    else:
        raise HTTPException(status_code=404, detail="No items found matching the query")