import logging
from datetime import datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)

SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]
PLANETS = [
    ("Солнце", swe.SUN), ("Луна", swe.MOON), ("Меркурий", swe.MERCURY),
    ("Венера", swe.VENUS), ("Марс", swe.MARS), ("Юпитер", swe.JUPITER),
    ("Сатурн", swe.SATURN), ("Уран", swe.URANUS), ("Нептун", swe.NEPTUNE),
    ("Плутон", swe.PLUTO),
]
ASPECTS = [
    ("соединение", 0, 8), ("секстиль", 60, 5),
    ("квадрат", 90, 6), ("трин", 120, 6), ("оппозиция", 180, 8),
]


@lru_cache(maxsize=256)
def geocode_place(place):
    geolocator = Nominatim(user_agent="ASTRA_natal_chart_bot/1.0 (astrology calculation)")
    location = geolocator.geocode(place, exactly_one=True, timeout=12)
    if not location:
        raise ValueError("Не удалось найти город. Уточни город и страну, например: Кишинёв, Молдова.")
    return float(location.latitude), float(location.longitude)


def zodiac_position(longitude):
    longitude = longitude % 360
    sign_index = int(longitude // 30)
    within_sign = longitude % 30
    degree = int(within_sign)
    minute = int(round((within_sign - degree) * 60))
    if minute == 60:
        degree += 1
        minute = 0
    return SIGNS[sign_index], degree, minute


def calculate_natal_chart(birth_date, birth_time, place):
    latitude, longitude = geocode_place(place)
    timezone_name = TimezoneFinder().timezone_at(lat=latitude, lng=longitude)
    if not timezone_name:
        raise ValueError("Не удалось определить часовой пояс этого места. Проверь название города.")
    local_dt = datetime.combine(birth_date, birth_time).replace(tzinfo=ZoneInfo(timezone_name))
    utc_dt = local_dt.astimezone(timezone.utc)
    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)

    flags = swe.FLG_MOSEPH | swe.FLG_SPEED
    positions = {}
    longitudes = {}
    for name, planet_id in PLANETS:
        values, _ = swe.calc_ut(jd, planet_id, flags)
        longitude_value = values[0] % 360
        longitudes[name] = longitude_value
        positions[name] = zodiac_position(longitude_value)

    cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'P')
    ascendant = zodiac_position(ascmc[0])
    mc = zodiac_position(ascmc[1])
    houses = []
    for index, cusp in enumerate(cusps, start=1):
        sign, degree, minute = zodiac_position(cusp)
        houses.append((index, sign, degree, minute))

    aspects = []
    names = list(longitudes)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            distance = abs((longitudes[first] - longitudes[second] + 180) % 360 - 180)
            for aspect_name, angle, orb in ASPECTS:
                deviation = abs(distance - angle)
                if deviation <= orb:
                    aspects.append((first, aspect_name, second, round(deviation, 1)))
                    break

    cusp_longitudes = [float(c) % 360 for c in cusps]
    return {
        "timezone": timezone_name,
        "positions": positions,
        "longitudes": longitudes,
        "cusp_longitudes": cusp_longitudes,
        "ascendant": ascendant,
        "mc": mc,
        "houses": houses,
        "aspects": aspects,
    }


def format_natal_chart(result, birth_date, birth_time, place):
    lines = [
        "🌙 ASTRA — натальная карта",
        f"Дата: {birth_date.strftime('%d.%m.%Y')}",
        f"Время: {birth_time.strftime('%H:%M')} (местное)",
        f"Место: {place}",
        f"Часовой пояс: {result['timezone']}",
        "",
        "✨ ПЛАНЕТЫ В ЗНАКАХ",
    ]
    for name, (sign, degree, minute) in result["positions"].items():
        lines.append(f"• {name}: {sign}, {degree}° {minute:02d}′")
    sign, degree, minute = result["ascendant"]
    lines.extend(["", f"⬆️ Асцендент: {sign}, {degree}° {minute:02d}′"])
    sign, degree, minute = result["mc"]
    lines.append(f"🎯 MC (середина неба): {sign}, {degree}° {minute:02d}′")
    lines.extend(["", "🏠 КУСПИДЫ 12 ДОМОВ"])
    for number, sign, degree, minute in result["houses"]:
        lines.append(f"• Дом {number}: {sign}, {degree}° {minute:02d}′")
    lines.extend(["", "🔗 ОСНОВНЫЕ АСПЕКТЫ"])
    if result["aspects"]:
        for first, aspect, second, orb in result["aspects"]:
            lines.append(f"• {first} — {aspect} — {second} (орбис {orb}°)")
    else:
        lines.append("• В выбранном наборе аспектов точных совпадений в заданных орбисах нет.")
    lines.extend([
        "",
        "ℹ️ Расчёт выполнен по астрономическим эфемеридам; интерпретация астрологических символов носит развлекательный и рефлексивный характер, не является научным описанием личности или прогнозом.",
    ])
    return "\n".join(lines)


# Краткие символические трактовки. Это авторский справочный текст ASTRA,
# а не научная оценка личности и не предсказание.
PLANET_MEANINGS = {
    "Солнце": "самовыражение, чувство собственного «я» и жизненная энергия",
    "Луна": "эмоциональные потребности, привычки и ощущение безопасности",
    "Меркурий": "мышление, обучение, речь и обмен информацией",
    "Венера": "симпатии, отношения, ценности и чувство гармонии",
    "Марс": "инициатива, смелость, желания и способ действовать",
    "Юпитер": "рост, мировоззрение, щедрость и поиск возможностей",
    "Сатурн": "ответственность, границы, дисциплина и долгосрочные задачи",
    "Уран": "независимость, обновление и нестандартные решения",
    "Нептун": "воображение, идеалы, вдохновение и чувствительность",
    "Плутон": "глубинные перемены, интенсивность и восстановление силы",
}
SIGN_STYLES = {
    "Овен": "прямо, энергично и с готовностью начинать первым",
    "Телец": "спокойно, основательно и с опорой на практический результат",
    "Близнецы": "через любознательность, общение и разнообразие идей",
    "Рак": "чутко, заботливо и с вниманием к эмоциональной безопасности",
    "Лев": "ярко, творчески и с желанием вкладывать сердце",
    "Дева": "внимательно, аналитично и стремясь всё улучшить",
    "Весы": "дипломатично, через сотрудничество и поиск равновесия",
    "Скорпион": "глубоко, интенсивно и не удовлетворяясь поверхностным",
    "Стрелец": "с энтузиазмом, широтой взглядов и тягой к развитию",
    "Козерог": "сдержанно, последовательно и ориентируясь на цель",
    "Водолей": "независимо, оригинально и с интересом к новому",
    "Рыбы": "интуитивно, образно и с высокой восприимчивостью",
}
HOUSE_THEMES = {
    1: "самопрезентации, внешнего поведения и личных начинаний",
    2: "личных ресурсов, денег, ценностей и самооценки",
    3: "общения, обучения, повседневных поездок и близкого окружения",
    4: "дома, семьи, корней и внутренней опоры",
    5: "творчества, романтики, удовольствий и самовыражения",
    6: "работы, повседневных привычек, навыков и заботы о себе",
    7: "партнёрства, брака, договорённостей и открытых союзов",
    8: "общих ресурсов, доверия, близости и глубоких перемен",
    9: "путешествий, высшего образования, убеждений и расширения кругозора",
    10: "карьеры, общественной роли, целей и репутации",
    11: "дружбы, сообществ, коллективных проектов и планов на будущее",
    12: "уединения, внутренней жизни, завершения циклов и скрытых процессов",
}


def find_house(longitude, cusp_longitudes):
    """Определяет дом по последовательным куспидам, включая переход через 0°."""
    value = longitude % 360
    for index, start in enumerate(cusp_longitudes):
        end = cusp_longitudes[(index + 1) % len(cusp_longitudes)]
        span = (end - start) % 360
        offset = (value - start) % 360
        if offset < span:
            return index + 1
    return 12


def format_interpretations(result):
    lines = ["", "📖 ИНТЕРПРЕТАЦИЯ ПЛАНЕТ В ЗНАКАХ И ДОМАХ"]
    for name, (sign, degree, minute) in result["positions"].items():
        house = find_house(result["longitudes"][name], result["cusp_longitudes"])
        meaning = PLANET_MEANINGS[name]
        style = SIGN_STYLES[sign]
        theme = HOUSE_THEMES[house]
        lines.extend([
            "",
            f"✦ {name} в {sign}, {house}-м доме",
            f"{meaning.capitalize()} здесь проявляются {style}.",
            f"Особое внимание может быть связано с темами {theme}.",
        ])
    lines.extend([
        "",
        "Примечание: астрологические трактовки символические; воспринимай их как повод для размышления, а не как установленный факт о себе.",
    ])
    return "\n".join(lines)
