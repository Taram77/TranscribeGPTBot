#telebot GPT Telegram bot created with ChatGPT
import os
import openai
import telebot
import whisper

print('Бот запущен!')

NUMBERS_ROWS = 6

openai.api_key = os.environ.get("OPENAI_API_KEY")
bot = telebot.TeleBot(os.environ.get("TELEGRAM_API_KEY"))

if not os.path.exists("users"):
    os.mkdir("users")

request_count = {}

# Function to generate a chat response using ChatGPT
def generate_chat_response(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        temperature=0.8,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=[" User:", " AI:"]
    )
    return response.choices[0].message["content"].strip()

@bot.message_handler(content_types=['text', 'voice'])
def msg(message):
    user_id = message.from_user.id

    if f"{user_id}.txt" not in os.listdir('users'):
        with open(f"users/{user_id}.txt", "x"):
            pass

    with open(f'users/{user_id}.txt', 'r', encoding='utf-8') as file:
        oldmes = file.read()

    if message.text == '/clear':
        with open(f'users/{user_id}.txt', 'w', encoding='utf-8') as file:
            file.write('')
        return bot.send_message(chat_id=user_id, text='История очищена!')

    if user_id in request_count and request_count[user_id] >= 10:
        return bot.send_message(chat_id=user_id, text='Твой лимит исчерпан!')

    try:
        send_message = bot.send_message(chat_id=user_id, text='Обрабатываю запрос, пожалуйста подождите!')

        if message.voice:
            voice_file_id = message.voice.file_id
            voice_info = bot.get_file(voice_file_id)
            voice_file = bot.download_file(voice_info.file_path)

            with open('audio.ogg', 'wb') as f:
                f.write(voice_file)

            model = whisper.load_model("base")
            result = model.transcribe("audio.ogg")
            transcription = result["text"]

            bot.edit_message_text(text=f'Ваш текст: {transcription}', chat_id=user_id, message_id=send_message.message_id)

            with open(f'users/{user_id}.txt', 'a+', encoding='utf-8') as file:
                file.write(f'[Voice] {transcription}\n')

            # Generate a response using ChatGPT
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f'Ваш текст: {transcription}'}
            ]
            chat_response = generate_chat_response(messages)

            # Send the response to the user
            bot.send_message(chat_id=user_id, text=chat_response)

        else:
            # Generate a response using ChatGPT
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": oldmes},
                {"role": "user", "content": f'Предыдущие сообщения: {oldmes}; Запрос: {message.text}'}
            ]
            chat_response = generate_chat_response(messages)

            bot.edit_message_text(text=chat_response, chat_id=user_id, message_id=send_message.message_id)

            with open(f'users/{user_id}.txt', 'a+', encoding='utf-8') as file:
                file.write(message.text.replace('\n', ' ') + '\n' + chat_response.replace('\n', ' ') + '\n')

        with open(f'users/{user_id}.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) >= NUMBERS_ROWS + 1:
            with open(f'users/{user_id}.txt', 'w', encoding='utf-8') as f:
                f.writelines(lines[2:])

        if user_id in request_count:
            request_count[user_id] += 1
        else:
            request_count[user_id] = 1

    except Exception as e:
        bot.send_message(chat_id=user_id, text=str(e))

bot.infinity_polling()
