from django.db import migrations


DIAGRAM_LEVELS = """<svg viewBox="0 0 860 130" xmlns="http://www.w3.org/2000/svg" font-family="'Noto Sans Thai','Segoe UI',sans-serif">
<defs><marker id="lvlArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#329632"/></marker></defs>
<text x="430" y="16" text-anchor="middle" font-size="15" font-weight="700" fill="#287a28">ระดับการจัดระเบียบของสิ่งมีชีวิต (จากหน่วยเล็กไปหน่วยใหญ่)</text>
<rect x="20" y="35" width="120" height="70" rx="14" fill="#eaf3e9" stroke="#329632" stroke-width="2"/>
<text x="80" y="75" text-anchor="middle" font-size="14" font-weight="700" fill="#287a28">โมเลกุล</text>
<line x1="140" y1="70" x2="158" y2="70" stroke="#329632" stroke-width="3" marker-end="url(#lvlArrow)"/>
<rect x="160" y="35" width="120" height="70" rx="14" fill="#eaf3e9" stroke="#329632" stroke-width="2"/>
<text x="220" y="75" text-anchor="middle" font-size="14" font-weight="700" fill="#287a28">เซลล์</text>
<line x1="280" y1="70" x2="298" y2="70" stroke="#329632" stroke-width="3" marker-end="url(#lvlArrow)"/>
<rect x="300" y="35" width="120" height="70" rx="14" fill="#eaf3e9" stroke="#329632" stroke-width="2"/>
<text x="360" y="75" text-anchor="middle" font-size="14" font-weight="700" fill="#287a28">เนื้อเยื่อ</text>
<line x1="420" y1="70" x2="438" y2="70" stroke="#329632" stroke-width="3" marker-end="url(#lvlArrow)"/>
<rect x="440" y="35" width="120" height="70" rx="14" fill="#eaf3e9" stroke="#329632" stroke-width="2"/>
<text x="500" y="75" text-anchor="middle" font-size="14" font-weight="700" fill="#287a28">อวัยวะ</text>
<line x1="560" y1="70" x2="578" y2="70" stroke="#329632" stroke-width="3" marker-end="url(#lvlArrow)"/>
<rect x="580" y="35" width="120" height="70" rx="14" fill="#eaf3e9" stroke="#329632" stroke-width="2"/>
<text x="640" y="70" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">ระบบ</text>
<text x="640" y="86" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">อวัยวะ</text>
<line x1="700" y1="70" x2="718" y2="70" stroke="#329632" stroke-width="3" marker-end="url(#lvlArrow)"/>
<rect x="720" y="35" width="120" height="70" rx="14" fill="#329632" stroke="#287a28" stroke-width="2"/>
<text x="780" y="75" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">สิ่งมีชีวิต</text>
</svg>"""

DIAGRAM_METHOD = """<svg viewBox="-40 -30 740 290" xmlns="http://www.w3.org/2000/svg" font-family="'Noto Sans Thai','Segoe UI',sans-serif">
<defs><marker id="sciArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#329632"/></marker></defs>
<text x="330" y="-12" text-anchor="middle" font-size="15" font-weight="700" fill="#287a28">วงจรวิธีการทางวิทยาศาสตร์</text>
<line x1="140" y1="60" x2="300" y2="60" stroke="#329632" stroke-width="3" marker-end="url(#sciArrow)"/>
<line x1="400" y1="60" x2="560" y2="60" stroke="#329632" stroke-width="3" marker-end="url(#sciArrow)"/>
<line x1="610" y1="110" x2="610" y2="150" stroke="#329632" stroke-width="3" marker-end="url(#sciArrow)"/>
<line x1="560" y1="200" x2="400" y2="200" stroke="#329632" stroke-width="3" marker-end="url(#sciArrow)"/>
<line x1="300" y1="200" x2="140" y2="200" stroke="#329632" stroke-width="3" marker-end="url(#sciArrow)"/>
<path d="M40,200 C -30,200 -30,60 40,60" fill="none" stroke="#329632" stroke-width="3" marker-end="url(#sciArrow)"/>
<circle cx="90" cy="60" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="90" y="65" text-anchor="middle" font-size="13.5" font-weight="700" fill="#287a28">สังเกต</text>
<circle cx="350" cy="60" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="350" y="65" text-anchor="middle" font-size="13.5" font-weight="700" fill="#287a28">ตั้งคำถาม</text>
<circle cx="610" cy="60" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="610" y="55" text-anchor="middle" font-size="13" font-weight="700" fill="#287a28">ตั้ง</text>
<text x="610" y="72" text-anchor="middle" font-size="13" font-weight="700" fill="#287a28">สมมติฐาน</text>
<circle cx="610" cy="200" r="50" fill="#329632" stroke="#287a28" stroke-width="2.5"/>
<text x="610" y="206" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">ทดลอง</text>
<circle cx="350" cy="200" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="350" y="195" text-anchor="middle" font-size="13" font-weight="700" fill="#287a28">วิเคราะห์</text>
<text x="350" y="212" text-anchor="middle" font-size="13" font-weight="700" fill="#287a28">ข้อมูล</text>
<circle cx="90" cy="200" r="50" fill="#eaf3e9" stroke="#329632" stroke-width="2.5"/>
<text x="90" y="206" text-anchor="middle" font-size="14" font-weight="700" fill="#287a28">สรุปผล</text>
</svg>"""

DIAGRAM_BIOMOLECULES = """<svg viewBox="0 0 850 250" xmlns="http://www.w3.org/2000/svg" font-family="'Noto Sans Thai','Segoe UI',sans-serif">
<text x="425" y="18" text-anchor="middle" font-size="15" font-weight="700" fill="#287a28">สารชีวโมเลกุล 4 กลุ่มหลัก (แบบจำลองอย่างง่าย)</text>

<rect x="15" y="35" width="190" height="200" rx="16" fill="#fff7ed" stroke="#f59e0b" stroke-width="2"/>
<path d="M110,60 L145,80 L145,120 L110,140 L75,120 L75,80 Z" fill="none" stroke="#f59e0b" stroke-width="4"/>
<circle cx="110" cy="100" r="6" fill="#f59e0b"/>
<text x="110" y="175" text-anchor="middle" font-size="13.5" font-weight="700" fill="#9a3412">คาร์โบไฮเดรต</text>
<text x="110" y="195" text-anchor="middle" font-size="10.5" fill="#9a3412">โครงสร้างวงแหวนน้ำตาล</text>
<text x="110" y="210" text-anchor="middle" font-size="10.5" fill="#9a3412">แหล่งพลังงานหลัก</text>

<rect x="220" y="35" width="190" height="200" rx="16" fill="#fefce8" stroke="#eab308" stroke-width="2"/>
<circle cx="315" cy="70" r="20" fill="#eab308"/>
<polyline points="303,90 315,105 303,120 315,135" fill="none" stroke="#eab308" stroke-width="4" stroke-linecap="round"/>
<polyline points="327,90 339,105 327,120 339,135" fill="none" stroke="#eab308" stroke-width="4" stroke-linecap="round"/>
<text x="315" y="175" text-anchor="middle" font-size="13.5" font-weight="700" fill="#854d0e">ลิพิด</text>
<text x="315" y="195" text-anchor="middle" font-size="10.5" fill="#854d0e">หัวชอบน้ำ + หางไม่ชอบน้ำ</text>
<text x="315" y="210" text-anchor="middle" font-size="10.5" fill="#854d0e">องค์ประกอบเยื่อหุ้มเซลล์</text>

<rect x="425" y="35" width="190" height="200" rx="16" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>
<polyline points="460,140 485,95 510,140 535,95 560,140" fill="none" stroke="#3b82f6" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="460" cy="140" r="9" fill="#3b82f6"/>
<circle cx="485" cy="95" r="9" fill="#3b82f6"/>
<circle cx="510" cy="140" r="9" fill="#3b82f6"/>
<circle cx="535" cy="95" r="9" fill="#3b82f6"/>
<circle cx="560" cy="140" r="9" fill="#3b82f6"/>
<text x="520" y="175" text-anchor="middle" font-size="13.5" font-weight="700" fill="#1e40af">โปรตีน</text>
<text x="520" y="195" text-anchor="middle" font-size="10.5" fill="#1e40af">สายกรดอะมิโนต่อกัน</text>
<text x="520" y="210" text-anchor="middle" font-size="10.5" fill="#1e40af">เอนไซม์ / โครงสร้าง</text>

<rect x="630" y="35" width="205" height="200" rx="16" fill="#faf5ff" stroke="#8b5cf6" stroke-width="2"/>
<path d="M665,60 C 700,80 700,100 665,120 C 700,140 700,160 665,180" fill="none" stroke="#8b5cf6" stroke-width="3.5"/>
<path d="M765,60 C 730,80 730,100 765,120 C 730,140 730,160 765,180" fill="none" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="672" y1="70" x2="758" y2="70" stroke="#c4b5fd" stroke-width="3"/>
<line x1="678" y1="100" x2="752" y2="100" stroke="#c4b5fd" stroke-width="3"/>
<line x1="672" y1="130" x2="758" y2="130" stroke="#c4b5fd" stroke-width="3"/>
<line x1="678" y1="160" x2="752" y2="160" stroke="#c4b5fd" stroke-width="3"/>
<text x="732" y="200" text-anchor="middle" font-size="13.5" font-weight="700" fill="#5b21b6">กรดนิวคลีอิก</text>
<text x="732" y="218" text-anchor="middle" font-size="10.5" fill="#5b21b6">DNA / RNA เก็บรหัสพันธุกรรม</text>
</svg>"""

DIAGRAM_CELL = """<svg viewBox="0 0 700 470" xmlns="http://www.w3.org/2000/svg" font-family="'Noto Sans Thai','Segoe UI',sans-serif">
<text x="350" y="22" text-anchor="middle" font-size="15" font-weight="700" fill="#287a28">โครงสร้างเซลล์สัตว์ (แบบจำลองอย่างง่าย)</text>

<ellipse cx="350" cy="255" rx="300" ry="195" fill="#eaf3e9" stroke="#329632" stroke-width="4"/>
<text x="350" y="70" text-anchor="middle" font-size="12.5" font-weight="700" fill="#287a28">เยื่อหุ้มเซลล์ (Cell Membrane)</text>

<circle cx="270" cy="230" r="82" fill="#a5d6a7" stroke="#287a28" stroke-width="3"/>
<circle cx="270" cy="230" r="26" fill="#287a28"/>
<text x="270" y="150" text-anchor="middle" font-size="12.5" font-weight="700" fill="#1b5e20">นิวเคลียส</text>
<text x="270" y="234" text-anchor="middle" font-size="9.5" font-weight="700" fill="#eaf3e9">นิวคลีโอลัส</text>

<ellipse cx="500" cy="150" rx="52" ry="26" fill="#fbbf24" stroke="#b45309" stroke-width="2.5" transform="rotate(-18 500 150)"/>
<path d="M470,150 Q500,140 530,150" fill="none" stroke="#b45309" stroke-width="2" transform="rotate(-18 500 150)"/>
<path d="M470,158 Q500,148 530,158" fill="none" stroke="#b45309" stroke-width="2" transform="rotate(-18 500 150)"/>
<text x="590" y="120" text-anchor="middle" font-size="12" font-weight="700" fill="#92400e">ไมโทคอนเดรีย</text>
<line x1="530" y1="140" x2="560" y2="122" stroke="#92400e" stroke-width="1.5"/>

<ellipse cx="480" cy="345" rx="48" ry="24" fill="#fbbf24" stroke="#b45309" stroke-width="2.5" transform="rotate(15 480 345)"/>
<path d="M452,345 Q480,336 508,345" fill="none" stroke="#b45309" stroke-width="2" transform="rotate(15 480 345)"/>

<path d="M380,190 Q400,180 420,190 Q440,200 460,190" fill="none" stroke="#3b82f6" stroke-width="3"/>
<path d="M375,205 Q395,195 415,205 Q435,215 455,205" fill="none" stroke="#3b82f6" stroke-width="3"/>
<path d="M370,220 Q390,210 410,220 Q430,230 450,220" fill="none" stroke="#3b82f6" stroke-width="3"/>
<text x="420" y="170" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e40af">ร่างแหเอนโดพลาซึม</text>

<path d="M470,255 Q510,248 470,238" fill="none" stroke="#8b5cf6" stroke-width="3"/>
<path d="M478,268 Q518,261 478,251" fill="none" stroke="#8b5cf6" stroke-width="3"/>
<path d="M486,281 Q526,274 486,264" fill="none" stroke="#8b5cf6" stroke-width="3"/>
<text x="560" y="275" text-anchor="middle" font-size="11.5" font-weight="700" fill="#5b21b6">กอลจิคอมเพล็กซ์</text>

<circle cx="150" cy="150" r="3" fill="#374151"/>
<circle cx="165" cy="170" r="3" fill="#374151"/>
<circle cx="140" cy="185" r="3" fill="#374151"/>
<circle cx="390" cy="140" r="3" fill="#374151"/>
<circle cx="405" cy="160" r="3" fill="#374151"/>
<circle cx="180" cy="130" r="3" fill="#374151"/>
<text x="150" y="120" text-anchor="middle" font-size="11.5" font-weight="700" fill="#374151">ไรโบโซม</text>

<circle cx="175" cy="330" r="32" fill="#fde68a" stroke="#ca8a04" stroke-width="2.5"/>
<text x="175" y="385" text-anchor="middle" font-size="11.5" font-weight="700" fill="#854d0e">แวคิวโอล</text>
</svg>"""

DIAGRAM_TRANSPORT = """<svg viewBox="0 0 700 350" xmlns="http://www.w3.org/2000/svg" font-family="'Noto Sans Thai','Segoe UI',sans-serif">
<defs><marker id="tArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#329632"/></marker></defs>

<line x1="350" y1="10" x2="350" y2="300" stroke="#d1d5db" stroke-width="1.5" stroke-dasharray="4,4"/>

<text x="175" y="25" text-anchor="middle" font-size="14.5" font-weight="700" fill="#287a28">การแพร่ (Diffusion)</text>
<line x1="175" y1="45" x2="175" y2="255" stroke="#6b7280" stroke-width="3" stroke-dasharray="7,5"/>
<circle cx="70" cy="65" r="6" fill="#f59e0b"/><circle cx="95" cy="90" r="6" fill="#f59e0b"/><circle cx="60" cy="110" r="6" fill="#f59e0b"/>
<circle cx="100" cy="130" r="6" fill="#f59e0b"/><circle cx="75" cy="150" r="6" fill="#f59e0b"/><circle cx="110" cy="170" r="6" fill="#f59e0b"/>
<circle cx="65" cy="190" r="6" fill="#f59e0b"/><circle cx="95" cy="210" r="6" fill="#f59e0b"/><circle cx="55" cy="230" r="6" fill="#f59e0b"/>
<circle cx="120" cy="80" r="6" fill="#f59e0b"/><circle cx="130" cy="150" r="6" fill="#f59e0b"/><circle cx="125" cy="220" r="6" fill="#f59e0b"/>
<circle cx="220" cy="100" r="6" fill="#f59e0b"/><circle cx="250" cy="160" r="6" fill="#f59e0b"/><circle cx="215" cy="210" r="6" fill="#f59e0b"/>
<line x1="60" y1="280" x2="290" y2="280" stroke="#329632" stroke-width="3" marker-end="url(#tArrow)"/>
<text x="175" y="300" text-anchor="middle" font-size="11" fill="#374151">โมเลกุลแพร่จากบริเวณเข้มข้นสูง → ต่ำ</text>
<text x="90" y="60" text-anchor="middle" font-size="10" fill="#92400e">เข้มข้นสูง</text>
<text x="255" y="60" text-anchor="middle" font-size="10" fill="#92400e">เข้มข้นต่ำ</text>

<text x="525" y="25" text-anchor="middle" font-size="14.5" font-weight="700" fill="#287a28">ออสโมซิส (Osmosis)</text>
<line x1="525" y1="45" x2="525" y2="255" stroke="#329632" stroke-width="4"/>
<circle cx="525" cy="80" r="2.5" fill="#329632"/><circle cx="525" cy="120" r="2.5" fill="#329632"/>
<circle cx="525" cy="170" r="2.5" fill="#329632"/><circle cx="525" cy="220" r="2.5" fill="#329632"/>
<circle cx="440" cy="70" r="3" fill="#3b82f6"/><circle cx="460" cy="100" r="3" fill="#3b82f6"/><circle cx="430" cy="130" r="3" fill="#3b82f6"/>
<circle cx="455" cy="160" r="3" fill="#3b82f6"/><circle cx="435" cy="190" r="3" fill="#3b82f6"/><circle cx="460" cy="220" r="3" fill="#3b82f6"/>
<circle cx="410" cy="90" r="7" fill="#f59e0b"/><circle cx="405" cy="200" r="7" fill="#f59e0b"/>
<circle cx="600" cy="70" r="7" fill="#f59e0b"/><circle cx="620" cy="110" r="7" fill="#f59e0b"/><circle cx="595" cy="150" r="7" fill="#f59e0b"/>
<circle cx="625" cy="190" r="7" fill="#f59e0b"/><circle cx="600" cy="225" r="7" fill="#f59e0b"/>
<line x1="480" y1="280" x2="580" y2="280" stroke="#3b82f6" stroke-width="3" marker-end="url(#tArrow)"/>
<text x="525" y="300" text-anchor="middle" font-size="11" fill="#374151">น้ำแพร่จากสารละลายเจือจาง → เข้มข้น</text>
<text x="440" y="60" text-anchor="middle" font-size="10" fill="#1e3a8a">สารละลายเจือจาง</text>
<text x="610" y="60" text-anchor="middle" font-size="10" fill="#1e3a8a">สารละลายเข้มข้น</text>
</svg>"""


DIAGRAMS_BY_TITLE = {
    "ธรรมชาติของสิ่งมีชีวิต": DIAGRAM_LEVELS,
    "การศึกษาชีววิทยาและวิธีการทางวิทยาศาสตร์": DIAGRAM_METHOD,
    "เคมีที่เป็นพื้นฐานของสิ่งมีชีวิต": DIAGRAM_BIOMOLECULES,
    "เซลล์ของสิ่งมีชีวิต": DIAGRAM_CELL,
    "การลำเลียงสารเข้าและออกจากเซลล์": DIAGRAM_TRANSPORT,
}


def seed_m4_diagrams(apps, schema_editor):
    Lesson = apps.get_model("reanBio", "Lesson")
    for title, svg in DIAGRAMS_BY_TITLE.items():
        Lesson.objects.filter(grade="m4", title=title).update(diagram_svg=svg)


def remove_m4_diagrams(apps, schema_editor):
    Lesson = apps.get_model("reanBio", "Lesson")
    Lesson.objects.filter(grade="m4", title__in=list(DIAGRAMS_BY_TITLE.keys())).update(diagram_svg="")


class Migration(migrations.Migration):

    dependencies = [
        ("reanBio", "0007_lesson_diagram_svg"),
    ]

    operations = [
        migrations.RunPython(seed_m4_diagrams, remove_m4_diagrams),
    ]
