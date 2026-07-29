# database/seed.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'fitness.db'

def seed():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. 插入一个测试用户（密码在实际项目中要哈希处理，这里仅示例）
    cursor.execute('''
        INSERT OR IGNORE INTO users (email, password_hash, username, age, gender, height, weight, experience, goal, training_days, default_training_days, place, equipments)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('test@example.com', 'hashedpassword123', '测试用户', 25, '男', 175.0, 70.0, '完全新手', '增肌', 3, '周一,周三,周五', '健身房', '哑铃,杠铃'))

    # 获取 user_id
    cursor.execute('SELECT user_id FROM users WHERE email = ?', ('test@example.com',))
    user_id = cursor.fetchone()[0]

    # 2. 插入伤病示例
    cursor.execute('INSERT INTO injuries (user_id, body_part, description) VALUES (?, ?, ?)',
                   (user_id, '左膝', '轻微不适，深蹲时疼痛'))

    # 3. 插入几个动作到动作库
    actions = [
        ('杠铃卧推', '胸部', '杠铃', 'https://example.com/bench_press.gif', '推类,肩主导'),
        ('深蹲', '腿部', '杠铃', 'https://example.com/squat.gif', '膝主导,下肢'),
        ('哑铃弯举', '手臂', '哑铃', 'https://example.com/curl.gif', '拉类,肘主导'),
        ('引体向上', '背部', '徒手', 'https://example.com/pullup.gif', '拉类,背主导')
    ]
    for name, muscle, eq, gif, tags in actions:
        cursor.execute('INSERT INTO action_lib (name, target_muscle, equipment, gif_url, tags) VALUES (?, ?, ?, ?, ?)',
                       (name, muscle, eq, gif, tags))

    # 获取动作ID
    cursor.execute('SELECT action_id FROM action_lib WHERE name = ?', ('杠铃卧推',))
    bench_id = cursor.fetchone()[0]
    cursor.execute('SELECT action_id FROM action_lib WHERE name = ?', ('深蹲',))
    squat_id = cursor.fetchone()[0]

    # 4. 插入一条计划（周一）
    from datetime import date, timedelta
    next_monday = date.today() + timedelta(days=(7 - date.today().weekday()))
    plan_date = next_monday.strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO plan_exercises (user_id, training_date, action_id, order_num, sets, reps, rest, weight_suggestion)
        VALUES (?, ?, ?, 1, 3, 10, '90秒', '80%极限')
    ''', (user_id, plan_date, bench_id))

    cursor.execute('''
        INSERT INTO plan_exercises (user_id, training_date, action_id, order_num, sets, reps, rest, weight_suggestion)
        VALUES (?, ?, ?, 2, 3, 12, '60秒', '80%极限')
    ''', (user_id, plan_date, squat_id))

    # 5. 插入一条训练记录
    cursor.execute('''
        INSERT INTO training_records (user_id, training_date, action_id, status, note, is_manually_modified)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (user_id, plan_date, bench_id, '已完成', '最后一组借力'))

    conn.commit()
    conn.close()
    print(f"测试数据插入完成！用户ID: {user_id}")

if __name__ == '__main__':
    seed()