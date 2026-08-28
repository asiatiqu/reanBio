from django.db import migrations


CHAPTER1_TITLE = "การศึกษาชีววิทยา"

# บทที่ 1 ตามสารบัญหนังสือเรียนจริง: 1.1, 1.2, 1.3
CHAPTER1_UPDATES = {
    "ธรรมชาติของสิ่งมีชีวิต": {
        "subtopic_code": "1.1",
        "new_title": "1.1 ธรรมชาติของสิ่งมีชีวิต",
    },
    "การศึกษาชีววิทยาและวิธีการทางวิทยาศาสตร์": {
        "subtopic_code": "1.2",
        "new_title": "1.2 การศึกษาชีววิทยาและวิธีการทางวิทยาศาสตร์",
    },
}

# หัวข้อเก่าที่ยังไม่ตรงกับโครงสร้างสารบัญจริง (จะทำใหม่ให้ตรงหัวข้อย่อยทีหลัง)
OLD_TITLES_TO_REMOVE = [
    "เคมีที่เป็นพื้นฐานของสิ่งมีชีวิต",
    "เซลล์ของสิ่งมีชีวิต",
    "การลำเลียงสารเข้าและออกจากเซลล์",
]

DIAGRAM_STEM = """<svg viewBox="-40 -30 740 290" xmlns="http://www.w3.org/2000/svg" font-family="'Noto Sans Thai','Segoe UI',sans-serif">
<defs><marker id="stemArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#329632"/></marker></defs>
<text x="330" y="-12" text-anchor="middle" font-size="15" font-weight="700" fill="#287a28">กระบวนการออกแบบเชิงวิศวกรรม (Engineering Design Process)</text>
<line x1="140" y1="60" x2="300" y2="60" stroke="#329632" stroke-width="3" marker-end="url(#stemArrow)"/>
<line x1="400" y1="60" x2="560" y2="60" stroke="#329632" stroke-width="3" marker-end="url(#stemArrow)"/>
<line x1="610" y1="110" x2="610" y2="150" stroke="#329632" stroke-width="3" marker-end="url(#stemArrow)"/>
<line x1="560" y1="200" x2="400" y2="200" stroke="#329632" stroke-width="3" marker-end="url(#stemArrow)"/>
<line x1="300" y1="200" x2="140" y2="200" stroke="#329632" stroke-width="3" marker-end="url(#stemArrow)"/>
<path d="M40,200 C -30,200 -30,60 40,60" fill="none" stroke="#329632" stroke-width="3" marker-end="url(#stemArrow)"/>
<circle cx="90" cy="60" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="90" y="55" text-anchor="middle" font-size="13" font-weight="700" fill="#287a28">ระบุ</text>
<text x="90" y="72" text-anchor="middle" font-size="13" font-weight="700" fill="#287a28">ปัญหา</text>
<circle cx="350" cy="60" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="350" y="55" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">รวบรวม</text>
<text x="350" y="72" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">ข้อมูล</text>
<circle cx="610" cy="60" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="610" y="50" text-anchor="middle" font-size="11.5" font-weight="700" fill="#287a28">ออกแบบ</text>
<text x="610" y="66" text-anchor="middle" font-size="11.5" font-weight="700" fill="#287a28">วิธีแก้</text>
<text x="610" y="82" text-anchor="middle" font-size="11.5" font-weight="700" fill="#287a28">ปัญหา</text>
<circle cx="610" cy="200" r="50" fill="#329632" stroke="#287a28" stroke-width="2.5"/>
<text x="610" y="195" text-anchor="middle" font-size="12" font-weight="700" fill="#ffffff">วางแผน &amp;</text>
<text x="610" y="211" text-anchor="middle" font-size="12" font-weight="700" fill="#ffffff">ลงมือสร้าง</text>
<circle cx="350" cy="200" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="350" y="195" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">ทดสอบ &amp;</text>
<text x="350" y="212" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">ประเมินผล</text>
<circle cx="90" cy="200" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="90" y="195" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">นำเสนอ</text>
<text x="90" y="212" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">ผลงาน</text>
</svg>"""

CONTENT_STEM = (
    "สะเต็มศึกษา (STEM Education) คือแนวทางการจัดการเรียนรู้ที่บูรณาการศาสตร์ 4 สาขาเข้าด้วยกัน ได้แก่ "
    "วิทยาศาสตร์ (Science) เทคโนโลยี (Technology) วิศวกรรมศาสตร์ (Engineering) และคณิตศาสตร์ (Mathematics) "
    "โดยเน้นให้ผู้เรียนนำความรู้จากทั้ง 4 ศาสตร์มาประยุกต์ใช้แก้ปัญหาในชีวิตจริงอย่างเป็นระบบ "
    "แทนที่จะเรียนรู้แต่ละวิชาแยกจากกัน\n\n"
    "หัวใจสำคัญของสะเต็มศึกษาคือ 'กระบวนการออกแบบเชิงวิศวกรรม' (Engineering Design Process) "
    "ซึ่งเป็นขั้นตอนคิดแก้ปัญหาอย่างเป็นระบบ ประกอบด้วย 6 ขั้นตอนหลัก ดังนี้\n\n"
    "1. ระบุปัญหา (Problem Identification) กำหนดปัญหาหรือความต้องการให้ชัดเจน พร้อมเงื่อนไขและข้อจำกัดที่เกี่ยวข้อง\n\n"
    "2. รวบรวมข้อมูลและแนวคิดที่เกี่ยวข้อง (Related Information) ศึกษาความรู้ทางวิทยาศาสตร์ คณิตศาสตร์ "
    "และเทคโนโลยีที่เกี่ยวข้องกับปัญหา รวมถึงค้นหาแนวทางแก้ปัญหาที่มีอยู่แล้ว\n\n"
    "3. ออกแบบวิธีการแก้ปัญหา (Design Solution) ระดมความคิด เสนอแนวทางแก้ปัญหาหลายแบบ แล้วเลือกแนวทางที่เหมาะสมที่สุด "
    "พร้อมร่างแบบหรือแผนผังคร่าวๆ\n\n"
    "4. วางแผนและดำเนินการแก้ปัญหา (Plan and Develop) วางแผนขั้นตอนการสร้างชิ้นงานอย่างละเอียด "
    "แล้วลงมือสร้างต้นแบบ (prototype) ตามแบบที่ออกแบบไว้\n\n"
    "5. ทดสอบ ประเมินผล และปรับปรุงแก้ไข (Testing and Evaluation) นำต้นแบบไปทดสอบว่าใช้งานได้ตามที่ต้องการหรือไม่ "
    "เก็บข้อมูลผลการทดสอบ แล้วนำมาปรับปรุงแก้ไขซ้ำจนกว่าจะได้ผลลัพธ์ที่น่าพอใจ ขั้นตอนนี้อาจต้องทำซ้ำหลายรอบ\n\n"
    "6. นำเสนอผลงาน (Presentation) นำเสนอวิธีการแก้ปัญหา ชิ้นงาน และผลการทดสอบให้ผู้อื่นรับทราบ "
    "พร้อมอธิบายเหตุผลของการออกแบบ\n\n"
    "ตัวอย่างการประยุกต์ใช้กระบวนการนี้ในวิชาชีววิทยา เช่น การออกแบบ 'เครื่องกรองน้ำอย่างง่ายจากวัสดุธรรมชาติ' "
    "นักเรียนอาจเริ่มจากระบุปัญหาว่าน้ำในชุมชนมีความขุ่น จากนั้นศึกษาความรู้เรื่องการกรองและสมบัติของวัสดุต่างๆ "
    "เช่น ทราย ถ่าน กรวด ออกแบบชั้นวัสดุกรองน้ำ สร้างต้นแบบ แล้วทดสอบความใสของน้ำที่กรองได้ "
    "ก่อนปรับปรุงลำดับชั้นวัสดุให้กรองน้ำได้สะอาดขึ้น\n\n"
    "การเรียนรู้ผ่านสะเต็มศึกษาช่วยฝึกทักษะการคิดวิเคราะห์ การแก้ปัญหาอย่างสร้างสรรค์ การทำงานร่วมกันเป็นทีม "
    "และการสื่อสารนำเสนอผลงาน ซึ่งเป็นทักษะสำคัญในศตวรรษที่ 21 ที่นำไปใช้ได้ทั้งในการเรียนและการทำงานจริงในอนาคต"
)


def restructure(apps, schema_editor):
    Lesson = apps.get_model("reanBio", "Lesson")

    # ลบหัวข้อเก่าที่ยังไม่ตรงกับสารบัญจริง (จะทำใหม่แยกตามหัวข้อย่อยของบทที่ 2-3 ทีหลัง)
    Lesson.objects.filter(grade="m4", title__in=OLD_TITLES_TO_REMOVE).delete()

    # อัปเดต 1.1 และ 1.2 ให้มีเลขหัวข้อย่อยและอยู่ในบทที่ 1
    for old_title, info in CHAPTER1_UPDATES.items():
        Lesson.objects.filter(grade="m4", title=old_title).update(
            title=info["new_title"],
            chapter=1,
            chapter_title=CHAPTER1_TITLE,
            subtopic_code=info["subtopic_code"],
        )
        # แก้ order ให้เรียงตามหัวข้อย่อย (1 หรือ 2)
        Lesson.objects.filter(grade="m4", title=info["new_title"]).update(
            order=int(info["subtopic_code"].split(".")[1])
        )

    # เพิ่มหัวข้อ 1.3 กิจกรรมสะเต็มศึกษาและกระบวนการออกแบบเชิงวิศวกรรม
    Lesson.objects.get_or_create(
        grade="m4",
        title="1.3 กิจกรรมสะเต็มศึกษาและกระบวนการออกแบบเชิงวิศวกรรม",
        defaults={
            "icon": "⚙️",
            "chapter": 1,
            "chapter_title": CHAPTER1_TITLE,
            "subtopic_code": "1.3",
            "order": 3,
            "duration_minutes": 45,
            "sub_lessons_count": 2,
            "description": "รู้จักสะเต็มศึกษาและฝึกใช้กระบวนการออกแบบเชิงวิศวกรรม 6 ขั้นตอนแก้ปัญหาอย่างเป็นระบบ",
            "content": CONTENT_STEM,
            "diagram_svg": DIAGRAM_STEM,
        },
    )


def reverse_restructure(apps, schema_editor):
    # ย้อนกลับแบบคร่าวๆ: ลบหัวข้อ 1.3 ที่เพิ่มใหม่ และคืนชื่อ 1.1/1.2 กลับเป็นชื่อเดิม
    Lesson = apps.get_model("reanBio", "Lesson")
    Lesson.objects.filter(
        grade="m4", title="1.3 กิจกรรมสะเต็มศึกษาและกระบวนการออกแบบเชิงวิศวกรรม"
    ).delete()
    for old_title, info in CHAPTER1_UPDATES.items():
        Lesson.objects.filter(grade="m4", title=info["new_title"]).update(
            title=old_title, subtopic_code="", chapter_title=""
        )


class Migration(migrations.Migration):

    dependencies = [
        ("reanBio", "0009_alter_lesson_options_lesson_chapter_and_more"),
    ]

    operations = [
        migrations.RunPython(restructure, reverse_restructure),
    ]
