import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext, MessageHandler, filters, ApplicationBuilder, Updater, JobQueue, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

'''
# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
'''

# Выключаем логирование
logging.disable(logging.CRITICAL)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена из переменных окружения
bot_token = os.getenv('BOT_TOKEN')

# Определение состояний для ConversationHandler
ASK_NAME, QUESTION1, QUESTION2, QUESTION3, GET_DATA, RESULT = range(6)

# Вопросы и варианты ответов
questions = [
    "Выберите ваш знак зодиака",
    "Как вы считаете, <b>период ретроградного Меркурия</b> вам помогает или мешает?",
    "<i>Обладателям ретроградного Меркурия в натальной карте обычно везёт больше непосредственно в сам период ретроградного движения Меркурия, является достаточно продуктивным - с 4 по 29 августа 2024</i>\n\nЕсли вам интересно узнать, <b>какой у вас Меркурий в натальной карте от рождения</b>, то оставьте ваши данные: <i>дата, время и город рождения</i>.\nИ я вам пришлю ответ в личные сообщения."
    
]
options = [
    ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"],
    ["Помогает", "Мешает"],
    ["Отправить данные", "Нет, спасибо"]
]

# Описание результатов на основе ответов

results = {
    "Овен": {
        "description": "<i><u>ОВЕН</u></i>\n\nВ августе могут появиться вопросы, связанные с работой и здоровьем. Придётся вернуться к прошлым задачам, что-то переделать и улучшить. Какая-то проблема может напомнить о себе, которую придётся снова разрешать.Объявятся клиенты или коллеги из прошлого. С 1 по 5 августа следует быть осторожнее с тратами, могут быть непредвиденные расходы. Увеличивается количество поездок, учебы и общения. Также, вас ожидают трансформации в проектах, сообществах, в которых вы состоите. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('OVEN')
    },
    "Телец": {
        "description": "<i><u>ТЕЛЕЦ</u></i>\n\nВ августе может вернуться прошлая любовь, ваши бывшие напомнят о себе. Снова может возобновиться роман, отношения. Вы пересмотрите своё дело жизни, проект, творчество. Возможно, вернетесь к старому хобби. Либо решите обновить знания и улучшить навыки для своего дела. Вы можете отправиться в отпуск в уже знакомое место, где ранее отдыхали. Детская тема также будет для вас актуальна. Отличное время, чтобы проверить здоровье перед беременностью. С 1 по 4 августа будьте осторожны в желании изменить что-то во внешности. Лучше это отложить на сентябрь. Весь август увеличиваются траты, лучше пересмотреть расходы. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('TELEC')
    },
    "Близнецы": {
        "description": "<i><u>БЛИЗНЕЦЫ</u></i>\n\nВ августе вернутся вопросы, связанные с домом, семьёй. Нужно будет что-то переделать, завершить прошлые задачи. Например, переоформить с родителями или мамой какие-то документы. Решить вопросы с недвижимостью, что-то перестроить. Август подходит для выбора и осмотра недвижимости. Но покупку и оформление сделки отложите до сентября. Можно купить что-то недорогое или по скидке, либо то, что было давно в планах. Весь месяц захочется действовать и заявлять о себе, но постоянно будет что-то мешать. Например, прошлые рабочие обстоятельства. Особенно с 15 по 23 августа - домашние дела не дают реализоваться вашим рабочим планам. Вы задумаетесь об обучении или поездке за границу, в надежде на трансформации. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('BLIZNECU')
    },
    "Рак": {
        "description": "<i><u>РАК</u></i>\n\nВ августе вы вернетесь к прошлым обучениям и коммуникациям. Вам захочется улучшить знания и навыки, возможно, решитесь на пересдачу экзамена. Месяц отлично подходит для этого. Вы задумаетесь о возобновлении общения с родственниками, сёстрами и братьями. Возможно придется переделывать документы. Будьте внимательны. Хорошее время, для того, чтобы отправить в сервис или на диагностику вашу технику - авто, гаджеты и т.д.. Намечается небольшая поездка, которая уже была в прошлом, возможен, даже переезд. Но перемещения могут не оправдать ваших ожиданий. Трансформации в теме финансов, возможно, придётся вернуть или дать в долг. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('RAK')
    },
    "Лев": {
        "description": "<i><u>ЛЕВ</u></i>\n\nВ августе вас посетят мысли об улучшении финансового положения. Вы задумаетесь о смене работы, перераспределении финансовых ресурсов. Т.к. возможна задержка выплат, либо сверх траты. Будьте внимательны. Если думали что-то продать, то месяц отлично подходит для этого. Хорошо проанализировать свою работу, переосмыслить свои действия. У вас появится снова второй шанс для важных изменений. Возможно, произойдёт переоценка ценностей, вы сможете заглянуть в прошлое, благодаря, работе с помогающим специалистом. Не пренебрегайте этим. Ожидают трансформации в личной и партнёрской теме. с 1 по 5 августа захочется что-то резко изменить в работе, но лучше это отложить до сентября. Увеличивается количество общения через соц.сети, сообщества. Возможна организация совместного проекта с другими объединениями, присутствует тема заграницы. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('LEV')
    },
    "Дева": {
        "description": "<i><u>ДЕВА</u></i>\n\nАвгуст - важный месяц для вас, мах трансформационный. Вы почувствуете изменения больше, чем другие знаки. Вы снова вернетесь к вопросам внешности, собственному позиционированию, и своему имиджу. Отличный месяц - поиска себя и работы со стилистом. Можно возобновить то, что уже ранее начинали в вопросах внешности и личного бренда. Возможна смена важных личных данных, документов - ваших имени и фамилии. Также, нужно быть готовым, что любые договорённости могут отложиться на неопределенный срок. Встречи и переговоры могут отменяться. Лучше всего какие-либо сотрудничества отложить до сентября. Ожидаются изменения в рабочей сфере, желание отправиться в поездку или на обучение. Вам захочется активно проявляться и действовать в рабочих вопросах и карьере, но это не всегда будет сделать просто. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('DEVA')
    },
    "Весы": {
        "description": "<i><u>ВЕСЫ</u></i>\n\nВ августе вам придётся вернуться в прошлое, чтобы что-то окончательно завершить. Возможно, вы сможете найти потерянную вещь, важную информацию или получите сообщение из прошлого. Может состояться поездка, которая поможет поставить точку в важных размышлениях. Но, и где потребуется быть мах активным, чтобы преодолеть трудности. Месяц отлично подходит для поддержания здоровья и нормализации питания. Хорошо заняться восстановлением тела и души. Стоит закончить незавершенные дела. Также, ожидаются трансформации с любовной сфере и в любимом деле. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('VESU')
    },
    "Скорпион": {
        "description": "<i><u>СКОРПИОН</u></i>\n\nВ августе ожидаются встречи со старыми знакомыми и друзьями. Возможно, вы организуете какое-то общее дело или объедините единомышленников. Месяц отлично подходит для того, чтобы снова вернуться к прошлым мечтам и желаниям. Отправляйтесь на конференции и семинары, освежите знания. Улучшите и внесите изменения в ваши социальные сети. Стоит что-то точно переделать. Приготовьтесь к тому, что возможны переносы планов, всё может меняться. Ожидаются какие-либо трансформации в семейно-родительской теме, вопросы связанные с домом. Финансовая сфера потребует активных действий, с расчетом на будущее. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('SKORPION')
    },
    "Стрелец": {
        "description": "<i><u>СТРЕЛЕЦ</u></i>\n\nВ августе ожидаются трансформации в работе и карьере. Произойдут какие-либо изменения в статусе. Это может касаться, и бизнес-партнёрства, так и романтических отношений. Также, придётся вернуться к незавершенным делам, связанные с документами. Появятся ситуации и события, которые необходимо разрешить с родителями, преимущественно с отцом. Произойдут изменения в коммуникациях, учебе и поездках. Более активных действий, с вашей стороны, потребуют личные и партнёрский отношения. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('STRELEC')
    },
    "Козерог": {
        "description": "<i><u>КОЗЕРОГ</u></i>\n\nВ августе, возможно, придётся совершить поездку и вернуться в старое место. Надо пересмотреть и изменить что-то важное в своих действиях. Отличное время, чтобы вернуться к  обучению, пересдать экзамены, и что-либо обжаловать. Хорошим решением будет улучшить свои письменные работы, статьи, публикации и т.д.. Произойдут какие-либо изменения в финансовой сфере. С 1 по 5 августа и вторую половину месяца могут эмоционально задевать обстоятельства любовных отношений, детей, проектов, творчества или хобби. Весь август активных действий потребует рабочая сфера, возможно, придется что-то завершить.  Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('KOZEROG')
    },
    "Водолей": {
        "description": "<i><u>ВОДОЛЕЙ</u></i>\n\nВ августе особого внимания потребуют вопросы финансов и инвестиций. Будьте  осторожны в распределении ресурсов. Возможно, появится шанс вернуть или получить деньги обратно. Потребуется что-то обновить и пересмотреть в документах, особенно, финансовых, например, завещания. Хорошее время для переговоров с инвесторами, состоятельными влиятельными личностями. Могут происходить личные трансформации, возврат к прошлым травмам. Также, появится желание что-то изменить во внешности. Любые изменения стоит отложить до сентября. С 1 по 5 августа могут эмоционально затронуть вопросы связанные с семьей, домом, недвижимостью. Активных действий потребуют вопросы, связанные с любовной сферой, детьми, проектами, хобби.  Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('VODOLEJ')
    },
    "Рыбы": {
        "description": "<i><u>РЫБЫ</u></i>\n\nВ августе могут вернуться ваши бывшие бизнес или личные партнёры, или новости о них. Поэтому, есть вероятность, что вы возобновите прошлые совместные дела. Но будьте готовы, что любые внешние сделки купли-продажи, договоренности, коллаборации и т.д. могут переноситься и отменяться. В августе лучше ничего не покупать. Если есть необходимость, то можно продать, то, что было ранее запланировано. Месяц отлично подходит для пересмотра контрактов, сделок и договоренностей. Могут вернуться старые клиенты. С 1 по 5 августа изменений коснуться ваши поездки, обучения, коммуникации. Сфера недвижимости, дома, семьи, родителей потребует активных действий. Любые важные решения стоит предпринимать после 12 сентября, когда Меркурий полностью восстановит своё движение.",
        "image": os.getenv('RUBU')
    },
}

# Путь к локальному изображению для приветственного сообщения
#WELCOME_PHOTO_PATH = 'C:/Users/narym/Chatbots/test/test/IMG_0969.jpg'  # Замените на путь к вашему изображению
WELCOME_PHOTO_PATH = os.getenv('WELCOME_PHOTO_PATH')

# Функция для генерации inline клавиатуры
def create_inline_keyboard(options, row_width=2):
    keyboard = []
    for i in range(0, len(options), row_width):
        keyboard.append([InlineKeyboardButton(option, callback_data=option) for option in options[i:i+row_width]])
    return InlineKeyboardMarkup(keyboard)

# Функция для генерации стартовой inline клавиатуры
def start_keyboard():
    keyboard = [[InlineKeyboardButton("Прогноз на август", callback_data="start_survey")]]
    return InlineKeyboardMarkup(keyboard)

# Настройка доступа к Google Sheets
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('./test/turing-zone-413110-9196fc82c6f8.json', scope)
    client = gspread.authorize(creds)
    return client

# Запись данных в Google Sheets
def write_to_google_sheets(user_data):
    client = get_gspread_client()
    sheet = client.open("ChatBotBD").sheet1  # Замените на имя вашего листа

    # Подготовка данных для записи
    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_data['username'], user_data['telegram_account']] + user_data['answers'] + [user_data.get('addit_data', '')]
    sheet.append_row(row)

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> int:
    with open(WELCOME_PHOTO_PATH, 'rb') as photo:
        await context.bot.send_photo(
            chat_id=update.message.chat_id,
            photo=photo,
            caption='<b>ПРОГНОЗ на АВГУСТ для вашего ЗНАКА зодиака</b> 👇🏼\n\nНас ожидает непростой, но продуктивный месяц. Приближается <b>период ретроградного Меркурия</b>, который продлится весь август 😯\n\nУзнайте, что он вам принесёт ⏩️ поддержку или сложности❓\n\n+ Бонус 🎁👇🏼\n\n<b>Определю какой Меркурий в вашей натальной карте от рождения.</b> Именно его ретроградное положение окажет поддержку в сам период ретроградного Меркурия - с 4 по 29 августа 2024.\n\nУзнать прогноз на АВГУСТ 👇🏼',
            parse_mode='HTML',
            reply_markup=start_keyboard()
        )
    return ASK_NAME

# Функция для обработки начала опроса
async def start_survey(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text('Пожалуйста, введите ваше имя:')
    return ASK_NAME

# Функция для обработки имени пользователя
async def ask_name(update: Update, context: CallbackContext) -> None:
    context.user_data['username'] = update.message.text
    context.user_data['telegram_account'] = update.message.from_user.username  # Сохраняем аккаунт Telegram
    await update.message.reply_text(
        questions[0],
        reply_markup=create_inline_keyboard(options[0], row_width=3)  # Задаем 3 кнопки в ряду
    )
    return QUESTION1

# Функция для обработки завершения опроса и отправки результата

# Функция для обработки ответов на вопросы
async def handle_question(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    answers = context.user_data.setdefault('answers', [])
    answers.append(query.data)
    
    current_state = len(answers)
    
    if current_state < len(questions):  # Учитываем, что последний вопрос - это вопрос о данных
        await query.message.reply_text(
            questions[current_state],
            reply_markup=create_inline_keyboard(options[current_state]),
            parse_mode='HTML'
        )
        return QUESTION1 + current_state
    
    elif current_state == len(questions) and query.data == "Отправить данные":
        await query.message.reply_text(
            'Пожалуйста, введите данные:'
        )
        return GET_DATA

    else:
        first_answer = answers[0]
        result_description = results.get(first_answer, "Ваши ответы уникальны, и мы не можем дать конкретное описание.")
        
        if result_description:
            description = result_description['description']
            image_path = result_description['image']
        
            # Отправляем изображение
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=f'<b>Прогноз на август:</b>\n\n{description}',
                    parse_mode='HTML'
                )
        else:
            await query.message.reply_text(
                f'<b>Прогноз на август:</b>\n\n{result_description}',
                parse_mode='HTML'
            )

        write_to_google_sheets(context.user_data)
        context.user_data['answers'] = []
        return ConversationHandler.END
    
# Функция для обработки данных
async def get_addit_data(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    context.user_data['addit_data'] = user_input
    
    first_answer = context.user_data['answers'][0]
    result_description = results.get(first_answer, "Ваши ответы уникальны, и мы не можем дать конкретное описание.")
    
    if result_description:
        description = result_description['description']
        image_path = result_description['image']
        
        # Отправляем изображение
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=photo,
                caption=f'<b>Прогноз на август 2024:</b>\n\n{description}',
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            f'<b>Прогноз на август 2024:</b>\n\n{result_description}',
            parse_mode='HTML'
        )
    
    write_to_google_sheets(context.user_data)
    context.user_data['answers'] = []
    return ConversationHandler.END

# Функция для обработки отмены опроса
async def cancel(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        'Опрос прерван.'
    )
    return ConversationHandler.END

# Обработчик ошибок
async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f'Update {update} caused error {context.error}')

async def send_ping(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    await context.bot.send_message(chat_id="504662108", text="Ping!")

def main() -> None:
    application = ApplicationBuilder().token(bot_token).build()

    # Получаем JobQueue
    job_queue = application.job_queue

    if job_queue is None:
        print("JobQueue не инициализирован!")
        return

    job_queue.run_repeating(send_ping, interval=timedelta(minutes=240), first=timedelta(seconds=10), name="ping_job", data="chat_id")


    # Определение обработчика разговора с состояниями
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern='start_survey')],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            QUESTION1: [CallbackQueryHandler(handle_question, pattern='^(Овен|Телец|Близнецы|Рак|Лев|Дева|Весы|Скорпион|Стрелец|Козерог|Водолей|Рыбы)$')],
            QUESTION2: [CallbackQueryHandler(handle_question, pattern='^(Помогает|Мешает)$')],
            QUESTION3: [CallbackQueryHandler(handle_question, pattern='^(Отправить данные|Нет, спасибо)$')],
            GET_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_addit_data)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cancel))  # Обработка текстовых сообщений
    application.add_error_handler(error_handler)

    application.run_polling()
 
if __name__ == '__main__':
    main()
