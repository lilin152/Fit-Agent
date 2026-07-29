
import sqlite3

# 连接到本地文件（如果不存在会自动创建）
conn = sqlite3.connect('fitness.db')
cursor = conn.cursor()

# 创建用户表
# database/init_db.py
import sqlite3
from pathlib import Path

# 数据库文件放在当前脚本同目录下的 fitness.db
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / 'fitness.db'

def init_database():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. 用户表：存储账号、密码、个人资料
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT, #用户唯一的id
            email TEXT UNIQUE NOT NULL, #用户邮箱
            password_hash TEXT NOT NULL, #用户密码
            username TEXT, #用户昵称
            age INTEGER, #年龄
            gender TEXT, #性别
            height REAL,#身高
            weight REAL,#体重
            experience TEXT, #训练经验
            goal TEXT DEFAULT '增肌',#训练目标
            training_days INTEGER DEFAULT 3,#每周训练天数
            default_training_days TEXT DEFAULT '周一,周三,周五', #默认训练日
            place TEXT,#训练场所
            equipments TEXT,#可用器械
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP #创建时间
        )
    ''')

    # 2. 伤病表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS injuries (
            injury_id INTEGER PRIMARY KEY AUTOINCREMENT,#伤病唯一id
            user_id INTEGER NOT NULL,#用户id
            body_part TEXT NOT NULL,#受伤部位
            description TEXT,#伤病描述
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,#创建时间
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # 3. 动作库表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_lib (
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,#动作唯一id
            name TEXT NOT NULL,#动作名称
            target_muscle TEXT,#目标肌群
            equipment TEXT,#器械类型
            gif_url TEXT,#动作演示gif链接
            tags TEXT # 动作标签（逗号分隔）
        )
    ''')

    # 4. 训练计划动作表（按日期存储实际计划）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_exercises (
            plan_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT, #计划动作唯一id
            user_id INTEGER NOT NULL,#用户id
            training_date DATE NOT NULL,#训练日期
            action_id INTEGER NOT NULL,#动作id
            order_num INTEGER,#动作顺序
            sets INTEGER,#组数
            reps INTEGER,#重复次数
            rest TEXT,#休息时间
            weight_suggestion TEXT,#重量建议
            FOREIGN KEY (user_id) REFERENCES users(user_id), 
            FOREIGN KEY (action_id) REFERENCES action_lib(action_id) #
        )
    ''')

    # 5. 训练记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,#训练记录唯一id
            user_id INTEGER NOT NULL,#用户id
            training_date DATE NOT NULL,#训练日期
            action_id INTEGER NOT NULL,#动作id
            status TEXT NOT NULL CHECK(status IN ('已完成', '未完成', '部分完成')),#训练状态
            note TEXT,#训练备注
            is_manually_modified INTEGER DEFAULT 0,#是否手动修改过计划（0=否，1=是）
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,#创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,#更新时间
            FOREIGN KEY (user_id) REFERENCES users(user_id),# 外键约束
            FOREIGN KEY (action_id) REFERENCES action_lib(action_id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"数据库初始化完成：{DB_PATH}")

if __name__ == '__main__':
    init_database()
