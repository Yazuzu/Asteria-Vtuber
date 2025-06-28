MAX_HISTORY = 20
history = {}

def atualizar_historico(user_id, nova_msg):
    msgs = history.get(user_id, [])
    msgs.append(nova_msg)
    history[user_id] = msgs[-MAX_HISTORY:]
    return "\n".join(history[user_id])
