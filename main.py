import logging
import pandas as pd
from datetime import datetime
import json
from aiogram import Bot, Dispatcher, types, executor


class TimeTrackerBot:
    def __init__(self):
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
            self.api_token = config["API_TOKEN"]
            self.json_filename = config["JSON_FILENAME"]

        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.bot = Bot(token=self.api_token)
        self.dispatcher = Dispatcher(self.bot)

        # Определение столбцов для DataFrame и начальных данных
        self.columns = ["Username", "id", "start date", "start time", "end time", "seconds", "minutes"]
        self.data = []

        # Загрузка данных из JSON файла при инициализации
        self._load_data()

    def _load_data(self):
        try:
            # Загрузка данных из JSON файла
            with open(self.json_filename, "r", encoding="utf-8") as json_file:
                self.data = json.load(json_file)
        except FileNotFoundError:
            self.data = []

    def _save_data(self):
        # Сохранение данных в JSON файл
        with open(self.json_filename, "w", encoding="utf-8") as json_file:
            json.dump(self.data, json_file)

    async def start_tracking(self, message):
        user = message.from_user
        now = datetime.now().strftime("%d:%m:%Y %H:%M:%S")

        # Добавление данных о начале работы в список
        self.data.append({"id": user.id, "Username": user.first_name, "start date": now, "start time": "", "end time": "", "seconds": 0, "minutes": 0})
        self._save_data()

        await message.reply(
            f"Ты начал(а) работу в {now}.\nКогда закончишь, нажми кнопку 'Закончить'.")

    async def end_tracking(self, message):
        user = message.from_user
        now = datetime.now().strftime("%d:%m:%Y %H:%M:%S")

        for item in self.data:
            if item["id"] == user.id and item["start time"] == "":
                start_time = datetime.strptime(item["start date"], "%d:%m:%Y %H:%M:%S")
                end_time = datetime.strptime(now, "%d:%m:%Y %H:%M:%S")
                total_running_time = end_time - start_time
                total_running_seconds = total_running_time.seconds
                total_running_minutes = total_running_seconds // 60
                total_running_seconds %= 60

                item["start time"] = start_time.strftime("%H:%M:%S")
                item["end time"] = now
                item["seconds"] = total_running_seconds
                item["minutes"] = total_running_minutes
                break

        self._save_data()

        result_message = (
            f"Ты закончил(а) работу в <b>{now}</b>.\n"
            f"Время работы: <b>{total_running_minutes} мин {total_running_seconds} сек</b>.\n"
            "Спасибо за проделанную работу!"
        )
        await message.reply(result_message, parse_mode=types.ParseMode.HTML)

        # Создание DataFrame и сохранение в файл Excel
        df = pd.DataFrame(self.data, columns=self.columns)
        excel_filename = "timetracker.xlsx"
        df.to_excel(excel_filename, index=False)

    async def unknown(self, message):
        await message.reply("Извини, я не понимаю эту команду.")

    def main(self):
        # Назначение обработчиков сообщений
        self.dispatcher.message_handler(lambda message: message.text == "Начать")(self.start_tracking)
        self.dispatcher.message_handler(lambda message: message.text == "Закончить")(self.end_tracking)
        self.dispatcher.message_handler()(self.unknown)
        # Запуск бота
        executor.start_polling(self.dispatcher)


if __name__ == "__main__":
    bot = TimeTrackerBot()
    bot.main()
