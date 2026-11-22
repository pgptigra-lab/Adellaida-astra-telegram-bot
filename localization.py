"""Offline Thai and English presentation for ASTRA natal-chart results.

All translations are bundled locally. No translation API is called.
"""
SIGNS = {
    "Овен": ("เมษ", "Aries"), "Телец": ("พฤษภ", "Taurus"),
    "Близнецы": ("เมถุน", "Gemini"), "Рак": ("กรกฎ", "Cancer"),
    "Лев": ("สิงห์", "Leo"), "Дева": ("กันย์", "Virgo"),
    "Весы": ("ตุลย์", "Libra"), "Скорпион": ("พิจิก", "Scorpio"),
    "Стрелец": ("ธนู", "Sagittarius"), "Козерог": ("มังกร", "Capricorn"),
    "Водолей": ("กุมภ์", "Aquarius"), "Рыбы": ("มีน", "Pisces"),
}
PLANETS = {
    "Солнце": ("ดวงอาทิตย์", "Sun"), "Луна": ("ดวงจันทร์", "Moon"),
    "Меркурий": ("ดาวพุธ", "Mercury"), "Венера": ("ดาวศุกร์", "Venus"),
    "Марс": ("ดาวอังคาร", "Mars"), "Юпитер": ("ดาวพฤหัสบดี", "Jupiter"),
    "Сатурн": ("ดาวเสาร์", "Saturn"), "Уран": ("ดาวยูเรนัส", "Uranus"),
    "Нептун": ("ดาวเนปจูน", "Neptune"), "Плутон": ("ดาวพลูโต", "Pluto"),
}
ASPECTS = {
    "соединение": ("กุม", "Conjunction"), "секстиль": ("เซ็กซ์ไทล์", "Sextile"),
    "квадрат": ("ฉาก", "Square"), "трин": ("ตรีโกณ", "Trine"),
    "оппозиция": ("เล็ง", "Opposition"),
}
TH = {
    "title": "แผนภูมิดวงกำเนิด", "date": "วันเกิด", "time": "เวลาเกิด",
    "place": "สถานที่เกิด", "timezone": "เขตเวลา", "planets": "ตำแหน่งดาวในราศี",
    "asc": "ลัคนา", "mc": "จุดกลางฟ้า (MC)", "houses": "ตำแหน่งเรือนทั้ง 12",
    "aspects": "มุมสัมพันธ์ระหว่างดาว", "no_aspects": "ไม่พบมุมสัมพันธ์ในช่วงองศาที่กำหนด",
    "interpretation": "คำอธิบายดวงกำเนิด", "portrait": "ภาพรวมบุคลิกภาพ",
    "intro": "การอ่านนี้เป็นการตีความเชิงสัญลักษณ์เพื่อการสำรวจตนเอง ไม่ใช่ข้อเท็จจริงทางวิทยาศาสตร์หรือคำวินิจฉัย",
    "planet_house": "{planet} อยู่ในราศี{sign} เรือนที่ {house}",
    "house_theme": "เรือนนี้เกี่ยวข้องกับหัวข้อชีวิต เช่น ความสัมพันธ์ การเรียนรู้ การงาน และการพัฒนาตนเอง",
    "aspect_line": "{first} {aspect} {second} (ค่าคลาดเคลื่อน {orb}°)",
    "aspect_note": "มุมสัมพันธ์นี้อาจสะท้อนการทำงานร่วมกันหรือความตึงเครียดระหว่างประเด็นที่ดาวทั้งสองเป็นตัวแทน ลองพิจารณาร่วมกับประสบการณ์จริงของคุณ",
    "sun": "ตัวตนและเป้าหมาย", "moon": "ความต้องการทางอารมณ์",
    "mercury": "ความคิดและการสื่อสาร", "venus": "ความรักและคุณค่า",
    "mars": "แรงผลักดันและการลงมือทำ", "growth": "แนวทางพัฒนาตนเอง",
    "growth_text": "ใช้จุดแข็งอย่างสมดุล เปิดใจเรียนรู้ และพิจารณาการตัดสินใจจากสถานการณ์จริง",
    "disclaimer": "โหราศาสตร์เป็นศาสตร์เชิงความเชื่อและการตีความ ไม่ใช่วิธีประเมินบุคลิกภาพที่ได้รับการยืนยันทางวิทยาศาสตร์",
}
EN = {
    "title": "Natal Birth Chart", "date": "Birth date", "time": "Birth time",
    "place": "Birth place", "timezone": "Time zone", "planets": "PLANETS IN SIGNS",
    "asc": "Ascendant", "mc": "Midheaven (MC)", "houses": "THE 12 HOUSES",
    "aspects": "MAJOR ASPECTS", "no_aspects": "No aspects found within the selected orbs.",
    "interpretation": "CHART INTERPRETATION", "portrait": "PERSONALITY OVERVIEW",
    "intro": "This is a symbolic reading for self-reflection, not a scientific fact, diagnosis, or guaranteed prediction.",
    "planet_house": "{planet} in {sign}, house {house}",
    "house_theme": "This house relates to life themes such as relationships, learning, career, and personal development.",
    "aspect_line": "{first} {aspect} {second} (orb {orb}°)",
    "aspect_note": "This aspect may symbolize cooperation or tension between the themes represented by these planets. Consider it alongside your real-life experience.",
    "sun": "Identity and goals", "moon": "Emotional needs",
    "mercury": "Thinking and communication", "venus": "Love and values",
    "mars": "Drive and action", "growth": "Personal growth",
    "growth_text": "Use your strengths in a balanced way, stay open to learning, and make decisions in light of real circumstances.",
    "disclaimer": "Astrology is a belief-based symbolic practice, not a scientifically validated method of personality assessment.",
}

def format_localized_chart(result, birth_date, birth_time, place, language="th"):
    thai = language == "th"
    t = TH if thai else EN
    idx = 0 if thai else 1
    sign_name = lambda value: SIGNS.get(value, (value, value))[idx]
    planet_name = lambda value: PLANETS.get(value, (value, value))[idx]
    aspect_name = lambda value: ASPECTS.get(value, (value, value))[idx]
    lines = [
        f"🌙 ASTRA — {t['title']}",
        f"{t['date']}: {birth_date.strftime('%d.%m.%Y')}",
        f"{t['time']}: {birth_time.strftime('%H:%M')} (local)",
        f"{t['place']}: {place}",
        f"{t['timezone']}: {result['timezone']}",
        "", f"✨ {t['planets']}",
    ]
    for name, (sign, degree, minute) in result["positions"].items():
        lines.append(f"• {planet_name(name)}: {sign_name(sign)} {degree}° {minute:02d}′")
    sign, degree, minute = result["ascendant"]
    lines.extend(["", f"⬆️ {t['asc']}: {sign_name(sign)} {degree}° {minute:02d}′"])
    sign, degree, minute = result["mc"]
    lines.append(f"🎯 {t['mc']}: {sign_name(sign)} {degree}° {minute:02d}′")
    lines.extend(["", f"🏠 {t['houses']}"])
    for number, sign, degree, minute in result["houses"]:
        lines.append(f"• {number}: {sign_name(sign)} {degree}° {minute:02d}′")
    lines.extend(["", f"🔗 {t['aspects']}"])
    if result["aspects"]:
        for first, aspect, second, orb in result["aspects"]:
            lines.append("• " + t["aspect_line"].format(
                first=planet_name(first), aspect=aspect_name(aspect),
                second=planet_name(second), orb=orb))
    else:
        lines.append(t["no_aspects"])

    lines.extend(["", f"📖 {t['interpretation']}"])
    for name, (sign, degree, minute) in result["positions"].items():
        house = _house_for(result, name)
        lines.append("• " + t["planet_house"].format(
            planet=planet_name(name), sign=sign_name(sign), house=house))
        lines.append("  " + t["house_theme"])
    lines.extend(["", f"🧭 {t['portrait']}", t["intro"]])
    for key in ("sun", "moon", "mercury", "venus", "mars"):
        lines.append("• " + t[key])
    lines.append(t["growth_text"])
    if result["aspects"]:
        lines.extend(["", f"⚖️ {t['aspects']}"])
        for first, aspect, second, orb in sorted(result["aspects"], key=lambda item: item[3])[:5]:
            lines.append("• " + t["aspect_line"].format(
                first=planet_name(first), aspect=aspect_name(aspect),
                second=planet_name(second), orb=orb))
            lines.append("  " + t["aspect_note"])
    lines.extend(["", "ℹ️ " + t["disclaimer"]])
    return "\n".join(lines)

def _house_for(result, planet):
    value = result["longitudes"][planet] % 360
    cusps = result["cusp_longitudes"]
    for i, start in enumerate(cusps):
        span = (cusps[(i + 1) % len(cusps)] - start) % 360
        if (value - start) % 360 < span:
            return i + 1
    return 12
