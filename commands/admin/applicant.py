

def accept(bot, payload, editor_id, event_id):
    user_id = payload[1]
    bot.vk.admin.groups.approveRequest(group_id=bot.vk.group_id, user_id=user_id)
    add_info(bot, user_id)
    del_info(bot, user_id)
    bot.logger.info(f"Игрок {user_id} был принят редактором {editor_id}")
    bot.vk.show_snackbar(event_id, editor_id, f"{payload[2]} принят(а)")
    bot.vk.send(user_id, 'Заявка успешно принята! Не забудь ознакомиться с правилами:\n'
                         '>> https://vk.com/page-165101106_55801147 <<\n\nНапиши любое сообщение, '
                         'чтобы перейти к меню бота, или "помощь", чтобы узнать больше')
    del_del_send_msg(bot, editor_id)
    del_messages(bot, user_id)


def reject(bot, payload, editor_id, event_id):
    user_id = payload[1]
    bot.vk.admin.groups.removeUser(group_id=bot.vk.group_id, user_id=user_id)
    del_info(bot, user_id)
    bot.logger.info(f"Игрок {user_id} был отклонён редактором {editor_id}")
    bot.vk.show_snackbar(event_id, editor_id, f"{payload[2]} отклонен(а)")
    bot.vk.send(user_id, 'К сожалению, заявка была отклонена. Проверь, выполнены ли требования, правильные '
                         'ли даны ответы выше. Если ты допустил(а) ошибку, напиши "начать" и ответь на '
                         'вопросы заново.')
    del_messages(bot, user_id)


def del_messages(bot, user_id: int):
    sql = 'SELECT message_id, editor_id FROM requests WHERE user_id = {}'.format(user_id)
    msg_ids = bot.db.fetchall(sql)
    for line in msg_ids:
        bot.vk.del_message(line[1], line[0])


def get_cw_id(bot, user_id: int):
    sql = 'SELECT cw_id FROM Intro WHERE vk_id = {}'.format(user_id)
    return bot.db.fetchone(sql)[0]


def add_info(bot, user_id: int):
    cw_id = get_cw_id(bot, user_id)
    sql = 'INSERT INTO users (vk_id, cw_id) VALUES ({}, {})'.format(user_id, cw_id)
    bot.db.add(sql)


def del_info(bot, user_id: int):
    sql = 'DELETE FROM Intro WHERE vk_id = {}'.format(user_id)
    bot.db.add(sql)


def del_del_send_msg(bot, user_id: int):
    sql = 'DELETE FROM msg_to_del WHERE vk_id = {}'.format(user_id)
    bot.db.add(sql)
