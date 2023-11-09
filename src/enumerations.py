from enum import Enum

class Status(str, Enum):
    BEGIN = "BEGIN"
    DISCARD = "DISCARD"
    PLAY_ACTION = "PLAY"
    ACTION_DEFENSE_REQUEST = "ACTION_DEFENSE_REQUEST"
    PLAY_ACTION_DEFENSE = "PLAY_ACTION_DEFENSE"
    EXCHANGE_OFFER = "EXCHANGE_OFFER"
    EXCHANGE_RESPONSE = "EXCHANGE_RESPONSE"
    PLAY_EXCHANGE_DEFENSE = "PLAY_EXCHANGE_DEFENSE"
    SEDUCTION_OFFER = "SEDUCTION_OFFER"
    SEDUCTION_RESPONSE = "SEDUCTION_RESPONSE"

class Kind(str, Enum):
    ACTION = "Acción"
    DEFENSE = "Defensa"
    OBSTACLE = "Obstáculo"
    PANIC = "¡Pánico!"
    THETHING = "La Cosa"
    INFECTION = "¡Infección!"

class Role(str, Enum):
    HUMAN = "Humano"
    THING = "La Cosa"
    INFECTED = "Infectado"

class CardName(str, Enum):
    THE_THING = 'La Cosa' #0
    INFECTED = 'Infectado'
    FLAMETHROWER = 'Lanzallamas'
    ANALYSIS = 'Análisis'
    AXE = 'Hacha'
    SUSPICION = 'Sospecha'
    DETERMINATION = 'Determinación'
    WHISKY = 'Whisky'
    SWAP_PLACES = 'Cambio de lugar'
    WATCH_YOUR_BACK = 'Vigila tus espaldas'
    SEDUCTION = 'Seducción'
    BARRED_DOOR = 'Puerta atrancada' # 11
    YOU_BETTER_RUN = 'Más vale que corras'
    IM_OK_HERE = 'Aquí estoy bien' # 13
    TERRIFYING = "Aterrador"
    NO_THANKS = 'No, gracias...'
    YOU_MISSED = 'Fallaste!'
    NO_BARBACUES = 'Nada de barbacoas' #17
    LOCKDOWN = 'Cuarentena' #18
    FULL_DISCLOSURE = 'Revelaciones'
    ROTTEN_ROPES = 'Cuerdas podridas'
    GET_OUT = 'Sal de aquí'
    FORGETFUL = 'Olvidadizo'
    ONE_TWO = 'Uno, dos...'
    THREE_FOUR = 'Tres, cuatro...'
    IS_THE_PARTY_HERE = 'Es aquí la fiesta?'
    JUST_BETWEEN_US = 'Que quede entre nosotros...'
    ROUND_AND_ROUND = 'Vuelta y vuelta'
    WHY_NOT_BE_FRIENDS = 'No podemos ser amigos?'
    BLIND_DATE = 'Cita a ciegas'
    UPS = 'Ups!'
