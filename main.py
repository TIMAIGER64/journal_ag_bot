from cgitb import text
from re import S
from imports import *
    
async def on_startup(_):
    print("BOT IS STARTING")


# START COMMAND
@dp.message_handler(commands=['start'])
async def get_command_start(message: types.Message):
    
    answer_start = f"Приветствую, {message.from_user.full_name}. С вами бот, который поможет тебе временно выйти из АГ! Команда 'HELP' расскажет о функционале"

    await message.answer(text=answer_start,
                         parse_mode="HTML",
                            reply_markup=kb_start)


# HELP COMMAND
@dp.callback_query_handler(text=['HELP'])
@dp.message_handler(text=['HELP'])
async def get_command_help(callback: types.CallbackQuery):

    help_answer = """
    <b>REGISTER</b> - <em>регистрация ученика (при условии проживания в общежитии АГ)</em>\n<b>LOGIN</b> - <em>вход в аккаунт ученика</em>"""
    
    await callback.message.answer(
                            text=help_answer,
                            parse_mode="HTML")


# USER INFO COMMAND
@dp.message_handler(text=['PROFILE'])
async def print_user_info(message: types.Message):
    chat_id=str(message.from_user.id)
    flag, index = check_log(chat_id)
    if flag:
        with open('users.csv', 'r') as file:
            user = file.readlines()[index]
            user = user.split(',')
            my_ans = f"""<b>Данные пользователя:</b>
        <em>Фамилия:</em> {user[1]},
        <em>Имя:</em> {user[2]},
        <em>Отчество:</em> {user[3]},
        <em>Комната:</em> {user[4]}
        <em>Твой st:</em> {user[5]}
        <em>Выход разрешён до</em> {user[6]}
        """
    else:
        my_ans = "<b>Вы не вошли в систему или не зарегистрированы в ней</b>.\n <em>Для подробной информации напишите /help</em>"
    await message.answer(chat_id, text=my_ans,parse_mode="HTML",)


# REGISTER COMMAND
@dp.callback_query_handler(text=['REGISTER'])
async def add_new_user(callback: types.CallbackQuery):
    text="""<b>Первый шаг регистрации:</b> \n<em>Введи своё ФИО через пробел</em>"""
    
    await bot.answer_callback_query(callback.id)

    await callback.message.answer(
                            text=text,
                            parse_mode="HTML",
                            reply_markup=ReplyKeyboardRemove())
    await register.FIO.set()

# STATE FIO
@dp.message_handler(state=register.FIO)
async def state1(message: types.Message, state=FSMContext):
    ans = message.text

    text="""<b>Второй шаг регистрации:</b> \n<em>Введи номер комнаты в общежитии</em>"""

    await state.update_data(FIO=ans)
    await message.answer(parse_mode="HTML",
                         text=text)
    await register.num_room.set()


# STATE ROOMs NUMBER
@dp.message_handler(state=register.num_room)
async def state2(message: types.Message, state=FSMContext):
    ans = message.text

    text="""<b>Третий шаг регистрации:</b> \n<em>Введи st-логин для подтверждения аккаунта по почте\nСкорее всего оно окажется в спаме</em>"""

    await state.update_data(num_room=ans)
    await message.answer(parse_mode="HTML",
                         text=text)
    await register.st_reg.set()

# STATE ST - LOGIN IN REGISTER
@dp.message_handler(state=register.st_reg) 
async def state3(message: types.Message, state=FSMContext):
    
    ans = message.text  
    global reg_active_code
    reg_active_code = send_mail(ans)

    text="""<b>Четвёртый шаг регистрации:</b> \n<em>Введи код подтверждения</em>"""

    await state.update_data(st_reg=ans)
    await message.answer(parse_mode="HTML",
                         text=text)
    await register.check_code_reg.set()


# STATE CHECK E-MAIL CODE IN REGISTER
@dp.message_handler(state=register.check_code_reg)
async def state4(message: types.Message, state=FSMContext):
    await state.update_data(check_code_reg = message.text)
    data = await state.get_data()
    if data['check_code_reg'] == reg_active_code:
        text="""<b>Регистрация прошла успешно.</b> \n<em>Система зафиксировала, что ты являешься учеником АГ!</em>"""
        FIO = data['FIO']
        FIO = FIO.split()
        surname, name, lastname = FIO[0], FIO[1], FIO[2]
        with open('users.csv', 'a') as file:
            file.write(f"{message.from_user.id},{surname},{name},{lastname},{data['num_room']},{data['st_reg']},22:00\n")    

        await message.answer(ext=text,
                              parse_mode="HTML",
                                reply_markup=kb_in)
    else:
        text="""Регистрация не удалась.\nВозможно вы ввели некорректный код активации"""
        await message.answer(ext=text,
                              parse_mode="HTML",
                                reply_markup=kb_start)


    await state.finish()


# LOGIN COMMAND
@dp.callback_query_handler(text='LOGIN')
async def get_command_login(callback: types.CallbackQuery):

    text="""<em>Введи st-логин для подтверждения по почте</em>"""

    await bot.answer_callback_query(callback.id)

    await callback.message.answer(
                            text=text,
                            parse_mode="HTML",
                            reply_markup=ReplyKeyboardRemove())
    await login.st_log.set()


# STATE ST - LOGIN IN LOGIN
@dp.message_handler(state=login.st_log)
async def state_log(message: types.Message, state=FSMContext):
    ans = message.text
    global index #Нужен global, чтобы в следующем handler обратиться
    flag, index = check_reg(ans)
    if flag:
        global log_active_code
        log_active_code = send_mail(ans)
        text="""<em>Введи код подтверждения по st-почте</em>"""
    else:
        text="""<em>Пользователь с таким st не зарегистрирован в нашей системе</em>"""
    

    await state.update_data(st_log=ans)
    
    await message.answer(parse_mode="HTML",
                         text=text)

    await login.check_code_login.set()


# STATE CHECK E-MAIL CODE IN LOGIN
@dp.message_handler(state=login.check_code_login)
async def check_code_login_def(message: types.Message, state=FSMContext):
    ans = message.text
    if log_active_code == ans:
        data = await state.get_data()
        fl, index = check_reg(data['st_log'])
        with open('users.csv', 'r') as fileREAD:
            data = fileREAD.readlines()
            user = data[index].split(',')
            user[0] = str(message.from_user.id)
            update_user = ""
            for charact in user:
                update_user += charact + ","
            update_user = update_user[:-1]
            data[index] = update_user
            users = ""
            for user in data:
                users += user
        with open('users.csv', 'w') as fileWRITE:
            fileWRITE.write(users)

        text="""<b>Авторизация прошла успешно.</b> \n<b>Добро пожаловать!</b>"""
    else:
        text="""<b>Вы не смогли войти в аккаунт.</b> \n<b>Скорее всего вы указали неправильный код активации</b>"""

    await message.answer(    text=text,
                             parse_mode="HTML",
                                reply_markup=kb_in)

    await state.finish()


# LOGOUT COMMAND
@dp.message_handler(text='LOGOUT')
async def get_command_login(message: types.Message):

    flag, index = check_log(str(message.from_user.id))
    if flag:
        with open('users.csv', 'r') as fileREAD:
            data = fileREAD.readlines()
            update_user = data[index].replace(str(message.from_user.id), '-1')
            data[index] = update_user
            update_data = ""
            for user in data:
                update_data += user
        with  open('users.csv', 'w') as fileWRITE:
            fileWRITE.write(update_data)
        
        text1="<b>УСПЕШНО!</b>"
        text="<em>Вы вышли из аккаунта!</em>"
    else:
        text1="<b>ОШИБКА!</b>"
        text="<em>Вы не в системе!</em>"

    await message.answer(text=text1,
                         reply_markup=ReplyKeyboardRemove(),
                         parse_mode="HTML")                  
    await message.answer(text=text,
                         parse_mode="HTML",
                            reply_markup=kb_start)


# ROUND CONNECT FROM USER
@dp.message_handler(text='COMMENT')
async def round_connect_from_users(message: types.Message):
    text="""<b>Обратная связь</b>\n<em>Если у вас есть пожелания, просьбы для улучшения нашего бота</em>\n<em>или вы нашли ошибку в работе бота, то оставте отзыв в Google Forms.</em>\n<em>Этот комментарий останеться </em><b>АНОНИМНЫМ:</b>\n<a href="https://forms.gle/ovk73RWEPuCqbCd36">Google Forms</a>"""

    await message.answer(text=text,
                         parse_mode="HTML")


# # EXIT COMMAND
# @dp.message_handler(text=['EXIT'])
# async def command_exit_(message: types.Message):
#     text="""<b>Укажите время выхода</b> \n<em>Формат: ЧЧ:ММ</em>"""

#     await message.answer(
#                   text=ext,
#                                 parse_mode="HTML",
#                             reply_markup=ReplyKeyboardRemove())
#     await exit.exit_time.set()


# EXIT COMMAND
@dp.message_handler(text='EXIT')
async def exit_calendar(message: types.Message):
    await message.answer(text="""<b>Выберите дату прихода в АГ</b>""",
                         parse_mode="HTML",
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(text="""<em>Если вы вернетесь этим же днём, \nвыберите сегодняшнюю дату:</em>""",
                         parse_mode="HTML",
                         reply_markup=await DialogCalendar().start_calendar())


# CALENDAR
@dp.callback_query_handler(dialog_cal_callback.filter())
async def process_dialog_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    if selected:
        await bot.answer_callback_query(callback_query.id)
        await exit.cal_date.set()
        await state.update_data(cal_date=date.strftime("%d.%m.%Y"))
        await callback_query.message.answer(f"""<b>Ты выбрал: {date.strftime("%d.%m.%Y")}</b>""", parse_mode="HTML")
        
        await command_exit_(callback_query.message)


# STATE cal_date
@dp.message_handler(state=exit.cal_date)
async def command_exit_(message: types.Message): 
    text="""<b>Укажите время выхода</b> \n<em>Формат: ЧЧ:ММ</em>"""

    await message.answer(text=text,
                         parse_mode="HTML",
                        reply_markup=ReplyKeyboardRemove())
    await exit.exit_time.set()


# STATE exit_time
@dp.message_handler(state=exit.exit_time)
async def state1(message: types.Message, state=FSMContext):
    ans = message.text

    text="""<b>Укажите время возвращения в АГ</b> \n<em>Формат: ЧЧ:ММ</em>"""

    await state.update_data(exit_time=ans)
    await message.answer(parse_mode="HTML",
                         text=text)
    await exit.entrance_time.set()


# STATE entrance_time
@dp.message_handler(state=exit.entrance_time)
async def state2(message: types.Message, state=FSMContext):
    ans = message.text

    text="""<b>Укажите причину выхода</b>"""

    await state.update_data(entrance_time = ans)
    await message.answer(parse_mode="HTML",
                         text=text)
    await exit.reason.set()

# STATE reason
@dp.message_handler(state=exit.reason) 
async def state3(message: types.Message, state=FSMContext):

    await state.update_data(reason=message.text)
    text="""<b>Вы можете идти</b> \n<em>Когда будете подходить к АГ, нажмите кнопку ENTRANCE</em>"""
    data = await state.get_data()
    
    with open('database.csv', 'a') as file: 
        file.write(f"{message.from_user.id},{data['exit_time']},{data['entrance_time']},{data['reason']},False,{data['cal_date']}\n")

    await message.answer(parse_mode="HTML",
                         text=text,
                            reply_markup=kb_out
                            )
    await exit.flag.set()

# STATE flag
@dp.message_handler(state=exit.flag)
async def state4(message: types.Message, state=FSMContext):
    text="<b>С возвращением!</b>"
    fl, index = check_log(message.from_user.id)
    with open('database.csv', 'r') as fileREAD:
        data = fileREAD.readlines()
        update_user = data[index].replace("False", "True")
        data[index] = update_user
        update_data = ""
        for user in data:
            update_data += user
    with  open('database.csv', 'w') as fileWRITE:
        fileWRITE.write(update_data)


    await message.answer(text=text,
                         parse_mode="HTML",
                            reply_markup=kb_in,
)

    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)