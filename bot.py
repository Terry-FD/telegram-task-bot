import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Each chat (group/private) has its own task list:
# { chat_id: [(task_text, msg_id, added_by)] }
tasks_by_chat = {}

def get_tasks_for(chat_id: int):
    return tasks_by_chat.setdefault(chat_id, [])

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Task Bot!\n"
        "Each group or chat has its own independent task list.\n\n"
        "Use /add <task> to add a task.\n"
        "Use /list to view tasks.\n"
        "Use /goto <number> to jump (reply) to the original task message.\n"
        "Use /done <number> to mark a task as completed and remove it.\n"
        "Use /clear to clear all tasks in this chat.\n"
        "Use /help to view all commands."
    )

# --- /help ---
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Task Bot Commands*\n\n"
        "🆕 `/add <task>` — Add a new task\n"
        "📄 `/list` — Show all current tasks\n"
        "🔎 `/goto <number>` — Reply to the original `/add` message for that task\n"
        "✅ `/done <number>` — Mark a task as completed and remove it\n"
        "🧹 `/clear` — Clear all tasks in *this chat*\n"
        "ℹ️ `/help` — Show this help message\n",
        parse_mode="Markdown"
    )

# --- /add ---
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    task_text = " ".join(context.args).strip()

    if not task_text:
        await update.message.reply_text("Please enter a task after the command, e.g. /add Buy milk")
        return

    msg_id = update.message.message_id
    user = update.effective_user
    added_by = f"@{user.username}" if user.username else (user.full_name or user.first_name or "Someone")

    tasks = get_tasks_for(chat_id)
    tasks.append((task_text, msg_id, added_by))
    await update.message.reply_text(f"✅ Task added: {task_text} (by {added_by})")

# --- /list ---
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tasks = get_tasks_for(chat_id)

    if not tasks:
        await update.message.reply_text("📭 No tasks yet.")
        return

    lines = [f"{i+1}. {t[0]} (by {t[2]})" for i, t in enumerate(tasks)]
    await update.message.reply_text("📝 Current tasks in this chat:\n" + "\n".join(lines))

# --- /goto ---
async def goto_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tasks = get_tasks_for(chat_id)

    if not tasks:
        await update.message.reply_text("📭 No tasks yet.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Please enter a task number, e.g. /goto 1")
        return

    index = int(context.args[0]) - 1
    if index < 0 or index >= len(tasks):
        await update.message.reply_text("❌ Invalid number. Use /list to check the task index.")
        return

    task_text, msg_id, added_by = tasks[index]
    await update.message.reply_text(f"📎 Original task (by {added_by}) 👇", reply_to_message_id=msg_id)

# --- /done ---
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tasks = get_tasks_for(chat_id)

    if not tasks:
        await update.message.reply_text("There are no tasks to complete. Add one with /add.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Please provide a valid number, e.g. /done 1")
        return

    index = int(context.args[0]) - 1
    if index < 0 or index >= len(tasks):
        await update.message.reply_text("That task number doesn’t exist. Use /list to check.")
        return

    finished_text, _, added_by = tasks.pop(index)
    await update.message.reply_text(f"✅ Completed and removed: {finished_text} (added by {added_by})")

# --- /clear ---
async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tasks_by_chat[chat_id] = []
    await update.message.reply_text("🧹 All tasks in this chat have been cleared.")

# --- Build app from env var token (for Render/Railway) ---
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_tasks))
app.add_handler(CommandHandler("goto", goto_task))
app.add_handler(CommandHandler("done", done_task))
app.add_handler(CommandHandler("clear", clear_tasks))

# --- Run main loop ---
async def main():
    print("🤖 Task Bot is running and listening for commands...")
    await app.run_polling()  # 新写法，自动初始化 + 启动 + 监听

if __name__ == "__main__":
    import asyncio

    print("🤖 Task Bot is running and listening for commands...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

