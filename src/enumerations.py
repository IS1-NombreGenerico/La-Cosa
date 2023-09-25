from enum import Enum

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
    THE_THING = 'La Cosa'
    INFECTED = 'Infectado!'
    FLAMETHROWER = 'Lanzallamas'
    ANALYSIS = 'Análisis'
    AXE = 'Hacha'
    SUSPICION = 'Sospecha'
    DETERMINATION = 'Determinación'
    WHISKY = 'Whisky'
    SWAP_PLACES = 'Cambio de lugar!'
    WATCH_YOUR_BACK = 'Vigila tus espaldas'
    SEDUCTION = 'Seducción'
    BARRED_DOOR = 'Puerta atrancada'
    YOU_BETTER_RUN = 'Más vale que corras!'
    IM_OK_HERE = 'Aquí estoy bien'
    TERRIFYING = "Aterrador"
    NO_THANKS = 'No, gracias...'
    YOU_MISSED = 'Fallaste!'
    NO_BARBACUES = 'Nada de barbacoas!'
    LOCKDOWN = 'Cuarentena'
    FULL_DISCLOSURE = 'Revelaciones'
    ROTTEN_ROPES = 'Cuerdas podridas'
    GET_OUT = 'Sal de aquí!'
    FORGETFUL = 'Olvidadizo'
    ONE_TWO = 'Uno, dos...'
    THREE_FOUR = 'Tres, cuatro...'
    IS_THE_PARTY_HERE = 'Es aquí la fiesta?'
    JUST_BETWEEN_US = 'Que quede entre nosotros...'
    ROUND_AND_ROUND = 'Vuelta y vuelta'
    WHY_NOT_BE_FRIENDS = 'No podemos ser amigos?'
    BLIND_DATE = 'Cita a ciegas'
    UPS = 'Ups!'
