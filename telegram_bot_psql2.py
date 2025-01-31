import asyncio
import psycopg2
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
import os
import requests

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Use environment variables for the database connection
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

# Function to get the public IP address
def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    return response.json()['ip']

link = f"http://{get_public_ip()}:8501"

send_results_running = False

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Connect to the PostgreSQL database
    connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
    cursor = connection.cursor()

    # Check if the user ID exists in the 'users' table
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if not result:
        # Insert the user ID into the 'users' table and update max_price, min_size, and min_rooms
        cursor.execute(
            "INSERT INTO users (user_id, max_price, min_size, min_rooms) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, 800, 1, 1)
        )
        connection.commit()

        # Create an InlineKeyboardButton with the user ID as text
        copy_button = InlineKeyboardButton(text=str(user_id), callback_data=str(user_id))

        # Create an InlineKeyboardMarkup with the copy button
        keyboard = InlineKeyboardMarkup([[copy_button]])

        # Send the user ID back to the user with the copy button
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Your user ID is:\n\n`{user_id}`\n\nYou can now setup your preferences at {link}\n\nRemember to copy your user ID (just tap it!) as you will need it to login to the interface.\nCommands I understand are:\n/Start - Initializes the bot\n/send_results - starts sending results according to your preferences until you\n/stop - the bot. Enjoy!\nOr you can\n/delete_account to do so.",
            reply_markup=keyboard
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"You are already registered!\nYour user ID is:\n\n`{user_id}`\n\nYou can use it to change your settings at {link}\nRemember to copy your user ID (just tap it!) as you will need it to login to the interface.\nCommands I understand are:\n/Start - Initializes the bot\n/send_results - starts sending results according to your preferences until you\n/stop - the bot. Enjoy!\nOr you can\n/delete_account to do so."
        )

    # Close the database connection
    cursor.close()
    connection.close()

logging.basicConfig(level=logging.DEBUG)

async def check_results(user_id, context):
    global send_results_running
    while send_results_running:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
        cursor = connection.cursor()

        # Retrieve user preferences from the "users" table
        cursor.execute("SELECT max_price, min_size, min_rooms, selected_cities, selected_neighborhoods FROM users WHERE user_id = %s", (user_id,))
        user_preferences = cursor.fetchone()

        if user_preferences is None:
            logging.debug(f"No user preferences found for user ID {user_id}")
            await asyncio.sleep(5)  # Wait for 30 seconds before checking again
            continue

        max_price = user_preferences[0]
        min_size = user_preferences[1]
        min_rooms = user_preferences[2]
        selected_cities = user_preferences[3]
        selected_neighborhoods = user_preferences[4]

        logging.debug(f"User preferences for user ID {user_id}: max_price={max_price}, min_size={min_size}, min_rooms={min_rooms}, selected_cities={selected_cities}, selected_neighborhoods={selected_neighborhoods}")

        # Retrieve unsent results from the "results" table based on user preferences
        cursor.execute("""
            SELECT id, address, rooms, size, price, link 
            FROM results 
            WHERE price <= %s 
              AND size >= %s 
              AND rooms >= %s 
              AND city = ANY(%s) 
              AND neighbourhood = ANY(%s) 
              AND id NOT IN (SELECT result_id FROM sent_results WHERE user_id = %s)
        """, (max_price, min_size, min_rooms, selected_cities, selected_neighborhoods, user_id))
        results = cursor.fetchall()

        logging.debug(f"Number of results found: {len(results)}")

        if len(results) == 0:
            await asyncio.sleep(5)  # Wait for 30 seconds before checking again
            continue

        for result in results:
            result_id = result[0]
            address = result[1]
            rooms = result[2]
            size = result[3]
            price = result[4]
            link = result[5]

            message_text = f"Address: {address}\nRooms: {rooms}\nSize: {size} m²\nPrice (Kaltmiete): {price} €\nLink: https://inberlinwohnen.de/wohnungsfinder{link}"

            # Send the result to the user
            await context.bot.send_message(chat_id=user_id, text=message_text)

            # Insert the sent result into the "sent_results" table
            cursor.execute("INSERT INTO sent_results (user_id, result_id, sent) VALUES (%s, %s, now())", (user_id, result_id))
            connection.commit()

        cursor.close()
        connection.close()
        await asyncio.sleep(5)  # Wait for 30 seconds before checking again

async def send_results(update: Update, context: CallbackContext):
    global send_results_running
    
    # Check if send_results is already running for this user
    if send_results_running:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="send_results is already running.")
        return
    
    send_results_running = True
    user_id = update.message.from_user.id
    
    # Start the check_results function in the background
    check_results_task = asyncio.create_task(check_results(user_id, context))
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="send_results started.")
    await check_results_task  # Wait for the check_results task to complete
    send_results_running = False
    await context.bot.send_message(chat_id=update.effective_chat.id, text="send_results stopped.")

async def stop(update: Update, context: CallbackContext):
    global send_results_running
    
    if send_results_running:
        send_results_running = False
        await context.bot.send_message(chat_id=update.effective_chat.id, text="send_results stopped.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="send_results is not running.")

async def delete_account(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # Connect to the PostgreSQL database
    connection = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
    cursor = connection.cursor()
    
    # Delete the user account from the 'users' table
    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM sent_results WHERE user_id = %s", (user_id,))
    connection.commit()
    
    # Close the database connection
    cursor.close()
    connection.close()
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Your account has been deleted.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    send_results_handler = CommandHandler('send_results', send_results)
    stop_handler = CommandHandler('stop', stop)
    delete_account_handler = CommandHandler('delete_account', delete_account)

    application.add_handler(delete_account_handler)
    application.add_handler(start_handler)
    application.add_handler(send_results_handler)
    application.add_handler(stop_handler)

    try:
        application.run_polling()
    except KeyboardInterrupt:
        application.stop()
