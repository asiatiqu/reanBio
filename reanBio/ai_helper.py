# 📌 ตัวช่วยเรียก Anthropic (Claude) API และระบบ RAG คลังความรู้ชีววิทยาอัจฉริยะ
#
# รองรับทั้ง:
#   1. โหมดเชื่อมต่อ Claude API (เมื่อตั้งค่า ANTHROPIC_API_KEY ใน .env)
#   2. โหมดคลังความรู้ชีววิทยาอัจฉริยะในระบบ (Local Biology RAG Engine) — ทำงานได้ทันทีแม้ยังไม่ได้ตั้งค่า API Key
#      โดยค้นหาและสังเคราะห์คำตอบจากบทเรียนชีววิทยาในระบบ + เอกสาร PDF อ้างอิง + คลังความรู้หลักสูตรชีววิทยา ม.ปลาย

import re
from django.conf import settings

# 📌 จำกัดขอบเขตคำถามให้เป็นเรื่องชีววิทยา/วิทยาศาสตร์ที่เกี่ยวข้องกับหลักสูตรมัธยมปลายเท่านั้น
SYSTEM_PROMPT = (
    "คุณคือผู้ช่วยตอบคำถามวิชาชีววิทยาสำหรับนักเรียนและคุณครูระดับมัธยมปลายในหลักสูตรไทย "
    "ตอบเป็นภาษาไทย กระชับ เข้าใจง่าย ยกตัวอย่างประกอบเมื่อช่วยให้เข้าใจง่ายขึ้น "
    "ตอบเฉพาะคำถามที่เกี่ยวข้องกับชีววิทยาหรือวิทยาศาสตร์ที่เกี่ยวข้องโดยตรงเท่านั้น "
    "ถ้าคำถามไม่เกี่ยวกับชีววิทยา ให้ปฏิเสธอย่างสุภาพและแนะนำให้ถามเรื่องชีววิทยาแทน "
    "ห้ามให้คำแนะนำทางการแพทย์เฉพาะบุคคล (เช่น วินิจฉัยอาการหรือสั่งยา) ให้แนะนำให้ไปพบแพทย์แทนในกรณีนั้น"
)

# 📌 คำสั่งเพิ่มเติมตามโหมดติวเตอร์ชีววิทยาแต่ละรูปแบบ
TUTOR_MODE_INSTRUCTIONS = {
    'explain': (
        "โหมดปัจจุบัน: [📖 อธิบายละเอียดเข้าใจง่าย] "
        "จงอธิบายแนวคิดทางชีววิทยาอย่างเป็นลำดับขั้น ใช้ภาษาที่นักเรียน ม.ปลาย เข้าใจง่าย "
        "เปรียบเทียบกับสิ่งรอบตัว และสรุปประเด็นสำคัญท้ายคำตอบ"
    ),
    'exam_prep': (
        "โหมดปัจจุบัน: [🎯 ติวเข้มเน้นจุดออกสอบ] "
        "จงอธิบายโดยเน้นจุดที่ออกข้อสอบชีววิทยา ม.ปลาย และ A-Level บ่อยที่สุด "
        "ชี้จุดหลอกหรือสิ่งที่นักเรียนมักจำสับสน และแถมโจทย์ปรนัยสั้นๆ 1 ข้อพร้อมเฉลยท้ายคำตอบ"
    ),
    'socratic': (
        "โหมดปัจจุบัน: [🧠 ชวนคิดวิเคราะห์ทีละขั้น] "
        "จงสอนแบบ Socratic Method โดยอธิบายหลักการตั้งต้น ให้คำใบ้เชื่อมโยงเหตุและผลทางชีววิทยา "
        "และตั้งคำถามชวนคิดต่อท้ายเพื่อให้ผู้เรียนได้ฝึกวิเคราะห์ด้วยตัวเอง"
    ),
    'summary': (
        "โหมดปัจจุบัน: [⚡ สรุปย่อ & เทคนิคช่วยจำ] "
        "จงสรุปเนื้อหาชีววิทยาเป็นข้อๆ (Bullet points) เปรียบเทียบความแตกต่างให้เห็นชัดเจน "
        "และให้เทคนิคช่วยจำ (Mnemonic / คำคล้องจอง / รากศัพท์ชีววิทยา) ที่จำไปใช้ในห้องสอบได้ทันที"
    ),
}

MAX_QUESTION_LENGTH = 800  # 📌 กันคำถามยาวเกินไป (ทั้งเรื่องค่าใช้จ่าย API และ UX)
MAX_HISTORY_TURNS = 8  # 📌 จำนวนข้อความย้อนหลังสูงสุดที่ส่งเข้าบริบทการสนทนาต่อเนื่อง


class AskAIError(Exception):
    """เกิดข้อผิดพลาดตอนเรียก AI (ยังไม่ได้ตั้งค่า key, เรียกไม่สำเร็จ, ฯลฯ)"""
    pass


# 📌 ระบบค้นหาบริบทที่เกี่ยวข้อง (RAG แบบ Chunk-level)
RAG_NGRAM_SIZE = 4
RAG_TOP_K = 4
RAG_CHUNK_CHARS = 1500
RAG_MIN_SCORE = 0.12
RAG_MIN_OVERLAP = 2

# 📌 คำสำคัญที่บ่งบอกว่าเป็นคำถามนอกเรื่องชีววิทยาอย่างชัดเจน
NON_BIO_KEYWORDS = (
    'เขียนโค้ด', 'ภาษาซี', 'จาวาสคริปต์', 'หุ้น', 'คริปโต', 'บิตคอยน์', 'ดูดวง', 'หวย', 'แทงบอล',
    'แต่งกลอนรัก', 'ประวัติศาสตร์อยุธยา', 'ไวยากรณ์อังกฤษ', 'present simple', 'past simple',
)

# 📌 คลังความรู้หลักสูตรชีววิทยา ม.ปลาย (สสวท.) ในตัว สำหรับเสริม RAG เมื่อคำถามอยู่นอกเหนือบทเรียนที่เปิดอยู่
BIOLOGY_CORE_KNOWLEDGE = [
    {
        'id': 'bio-core-cell',
        'title': 'โครงสร้างและหน้าที่ของเซลล์ (Cell Structure & Organelles)',
        'badge': 'หลักสูตรชีววิทยา ม.4',
        'keywords': ['เซลล์', 'ออร์แกเนลล์', 'นิวเคลียส', 'ไมโทคอนเดรีย', 'คลอโรพลาสต์', 'ไรโบโซม', 'ร่างแหเอนโดพลาซึม', 'กอลจิ', 'ไลโซโซม', 'ผนังเซลล์', 'เยื่อหุ้มเซลล์', 'เซลล์พืช', 'เซลล์สัตว์', 'ยูแคริโอต', 'โพรแคริโอต'],
        'content': (
            "เซลล์แบ่งออกเป็น 2 ประเภทหลัก คือ โพรแคริโอต (Prokaryote เช่น แบคทีเรีย และสาหร่ายสีเขียวแกมน้ำเงิน ไม่มีเยื่อหุ้มนิวเคลียส มีเฉพาะไรโบโซม 70S) "
            "และยูแคริโอต (Eukaryote เช่น พืช สัตว์ ฟังไจ โพรทิสต์ มีเยื่อหุ้มนิวเคลียสและออร์แกเนลล์ที่มีเยื่อหุ้ม)\n\n"
            "หน้าที่ของออร์แกเนลล์สำคัญ:\n"
            "• นิวเคลียส (Nucleus): ศูนย์ควบคุมการทำงานของเซลล์และเก็บสารพันธุกรรม (DNA)\n"
            "• ไมโทคอนเดรีย (Mitochondria): มีเยื่อหุ้ม 2 ชั้น ทำหน้าที่สลายสารอาหารระดับเซลล์เพื่อสร้างพลังงาน ATP\n"
            "• คลอโรพลาสต์ (Chloroplast): มีเยื่อหุ้ม 2 ชั้น พบในเซลล์พืชและสาหร่าย ทำหน้าที่สังเคราะห์ด้วยแสง\n"
            "• ไรโบโซม (Ribosome): ไม่มีเยื่อหุ้ม ทำหน้าที่สังเคราะห์โปรตีน\n"
            "• ร่างแหเอนโดพลาซึมแบบขรุขระ (RER): มีไรโบโซมเกาะ สร้างโปรตีนส่งออกนอกเซลล์ ส่วนแบบเรียบ (SER) สร้างลิพิดและกำจัดสารพิษ\n"
            "• กอลจิคอมเพล็กซ์ (Golgi complex): ดัดแปลง เติมคาร์โบไฮเดรต และบรรจุโปรตีนใส่ถุงเวสิเคิล\n"
            "• ไลโซโซม (Lysosome): มีเยื่อหุ้ม 1 ชั้น พบเฉพาะในเซลล์สัตว์ บรรจุเอนไซม์ย่อยสลายสิ่งแปลกปลอมและออร์แกเนลล์ที่เสื่อมสภาพ\n\n"
            "ความแตกต่างสำคัญ: เซลล์พืชมีผนังเซลล์ (Cell wall จากเซลลูโลส), คลอโรพลาสต์ และแวคิวโอลขนาดใหญ่ (Central vacuole) แต่ไม่มีเซนทริโอลและไลโซโซม ส่วนเซลล์สัตว์ไม่มีผนังเซลล์และไม่มีคลอโรพลาสต์ แต่มีเซนทริโอลและไลโซโซม"
        ),
        'exam_tip': "ข้อสอบมักหลอกเรื่องจำนวนชั้นของเยื่อหุ้มออร์แกเนลล์: เยื่อหุ้ม 2 ชั้น = นิวเคลียส, ไมโทคอนเดรีย, คลอโรพลาสต์ | ไม่มีเยื่อหุ้ม = ไรโบโซม, เซนทริโอล, ไซโทสเกเลตัน | ที่เหลือมีเยื่อหุ้ม 1 ชั้น",
        'mnemonic': "จำเยื่อหุ้ม: 'ไร้เยื่อ = ไร-เซน-ไซ (ไรโบโซม เซนทริโอล ไซโทสเกเลตัน)' / 'สองชั้น = นิว-ไม-คลอ (นิวเคลียส ไมโทคอนเดรีย คลอโรพลาสต์)'",
    },
    {
        'id': 'bio-core-transport',
        'title': 'การลำเลียงสารเข้าและออกจากเซลล์ (Membrane Transport)',
        'badge': 'หลักสูตรชีววิทยา ม.4',
        'keywords': ['การลำเลียงสาร', 'ออสโมซิส', 'การแพร่', 'ฟาซิลิเทต', 'แอกทีฟทรานสปอร์ต', 'เอกโซไซโทซิส', 'เอนโดไซโทซิส', 'ฟาโกไซโทซิส', 'ไฮเพอร์โทนิก', 'ไฮโพโทนิก', 'ไอโซโทนิก', 'พลาสโมไลซิส'],
        'content': (
            "การลำเลียงสารผ่านเยื่อหุ้มเซลล์แบ่งเป็น:\n"
            "1. ไม่ใช้พลังงาน ATP (Passive transport): เคลื่อนที่จากความเข้มข้นสูงไปต่ำ\n"
            "   • การแพร่แบบธรรมดา (Simple diffusion): สารไม่มีขั้วหรือโมเลกุลเล็ก เช่น O2, CO2, กรดไขมัน ผ่านชั้นลิพิดได้โดยตรง\n"
            "   • การแพร่แบบฟาซิลิเทต (Facilitated diffusion): สารมีขั้วหรือไอออน เช่น กลูโคส กรดอะมิโน อาศัยโปรตีนตัวพา (Carrier/Channel protein)\n"
            "   • ออสโมซิส (Osmosis): การแพร่ของน้ำจากบริเวณที่มีความเข้มข้นของสารละลายต่ำ (น้ำมาก - Hypotonic) ไปยังบริเวณที่มีความเข้มข้นของสารละลายสูง (น้ำน้อย - Hypertonic) ผ่านเยื่อเลือกผ่าน\n"
            "2. ใช้พลังงาน ATP (Active transport): ลำเลียงสารจากความเข้มข้นต่ำไปสูง อาศัยโปรตีนตัวพาและพลังงาน ATP เช่น โซเดียม-โพแทสเซียมปั๊ม (Na+-K+ pump)\n"
            "3. การลำเลียงสารโมเลกุลใหญ่ด้วยถุงเวสิเคิล (Bulk transport): ใช้พลังงาน ATP แบ่งเป็น เอกโซไซโทซิส (Exocytosis - ส่งออกนอกเซลล์ เช่น การหลั่งเอนไซม์/ฮอร์โมน) และเอนโดไซโทซิส (Endocytosis - นำเข้าเซลล์ ได้แก่ Phagocytosis, Pinocytosis, Receptor-mediated endocytosis)"
        ),
        'exam_tip': "ระวังสับสน! เมื่อแช่เซลล์เม็ดเลือดแดงในสารละลาย Hypotonic น้ำจะออสโมซิสเข้าเซลล์จนเซลล์เต่งและแตก (Hemolysis) แต่เซลล์พืชไม่แตกเพราะมีผนังเซลล์ค้ำจุน (เกิดแรงดันเต่ง Turgor pressure)",
        'mnemonic': "จำง่าย: 'ไฮโพ = โพอง (น้ำเข้าเซลล์เต่ง)' / 'ไฮเพอร์ = เพ้อเหี่ยว (น้ำออกเซลล์เหี่ยว เกิด Plasmolysis)'",
    },
    {
        'id': 'bio-core-division',
        'title': 'การแบ่งเซลล์: ไมโทซิส (Mitosis) และไมโอซิส (Meiosis)',
        'badge': 'หลักสูตรชีววิทยา ม.4',
        'keywords': ['การแบ่งเซลล์', 'ไมโทซิส', 'ไมโอซิส', 'วัฏจักรเซลล์', 'อินเตอร์เฟส', 'โพรเฟส', 'เมทาเฟส', 'แอนาเฟส', 'เทโลเฟส', 'โครโมโซม', 'ครอสซิงโอเวอร์', 'เซลล์ร่างกาย', 'เซลล์สืบพันธุ์', 'mitosis', 'meiosis'],
        'content': (
            "วัฏจักรเซลล์ (Cell cycle) ประกอบด้วยระยะอินเตอร์เฟส (G1, S, G2 โดยมีการจำลอง DNA ในระยะ S) และระยะแบ่งนิวเคลียส (M phase):\n\n"
            "1. การแบ่งเซลล์แบบไมโทซิส (Mitosis):\n"
            "   • เกิดกับเซลล์ร่างกาย (Somatic cell) เพื่อเพิ่มจำนวนเซลล์และการเจริญเติบโต\n"
            "   • แบ่งนิวเคลียส 1 ครั้ง (Prophase -> Metaphase -> Anaphase -> Telophase)\n"
            "   • ได้เซลล์ใหม่ 2 เซลล์ ที่มีจำนวนชุดโครโมโซมเท่าเดิม (2n -> 2n) และมีพันธุกรรมเหมือนเซลล์ตั้งต้นทุกประการ\n\n"
            "2. การแบ่งเซลล์แบบไมโอซิส (Meiosis):\n"
            "   • เกิดกับเซลล์ต้นกำเนิดเซลล์สืบพันธุ์ (Germ cell) เพื่อสร้างเซลล์สืบพันธุ์ (Gamete)\n"
            "   • แบ่งนิวเคลียส 2 ครั้งต่อเนื่อง (Meiosis I และ Meiosis II)\n"
            "   • ในระยะ Prophase I มีการเข้าคู่กันของโครโมโซมคู่เหมือน (Synapsis) และเกิดการแลกเปลี่ยนชิ้นส่วนโครมาทิด (Crossing over) ทำให้เกิดความแปรผันทางพันธุกรรม\n"
            "   • ในระยะ Anaphase I โครโมโซมคู่เหมือน (Homologous chromosomes) แยกออกจากกัน ทำให้จำนวนชุดโครโมโซมลดลงครึ่งหนึ่ง\n"
            "   • สิ้นสุดได้เซลล์ใหม่ 4 เซลล์ ที่มีจำนวนชุดโครโมโซมลดลงครึ่งหนึ่ง (2n -> n)"
        ),
        'exam_tip': "จุดออกสอบบ่อยที่สุด: Crossing over เกิดในระยะ Prophase I ของไมโอซิสเท่านั้น! และการลดจำนวนชุดโครโมโซมจาก 2n เป็น n เกิดขึ้นทันทีหลังจบ Meiosis I (เพราะ Homologous chromosome แยกจากกันใน Anaphase I)",
        'mnemonic': "ลำดับระยะ M phase: 'P-M-A-T (โพร-เม-แอน-เท)' -> โพร(สร้างเส้นใย) เม(เรียงกึ่งกลาง) แอน(แยกออก) เท(ท้ายสุดได้นิวเคลียสใหม่)",
    },
    {
        'id': 'bio-core-enzyme-respiration',
        'title': 'เอนไซม์ พลังงาน และการหายใจระดับเซลล์ (Enzymes & Cellular Respiration)',
        'badge': 'หลักสูตรชีววิทยา ม.4',
        'keywords': ['เอนไซม์', 'พลังงานก่อกัมมันต์', 'การหายใจระดับเซลล์', 'ไกลโคไลซิส', 'วัฏจักรเครบส์', 'การถ่ายทอดอิเล็กตรอน', 'หมักกรดแลกติก', 'หมักแอลกอฮอล์', 'atp', 'nadh', 'fadh2'],
        'content': (
            "• เอนไซม์ (Enzyme): ตัวเร่งปฏิกิริยาชีวภาพที่ส่วนใหญ่เป็นโปรตีน ทำหน้าที่ลดพลังงานก่อกัมมันต์ (Activation energy: Ea) โดยไม่เปลี่ยนค่าพลังงานอิสระของปฏิกิริยา มีความจำเพาะต่อสารตั้งต้น (Substrate) ที่บริเวณเร่ง (Active site) ปัจจัยที่มีผลได้แก่ อุณหภูมิ, ค่า pH, ความเข้มข้นของเอนไซม์และสารตั้งต้น และตัวยับยั้งเอนไซม์ (Inhibitor)\n\n"
            "• การหายใจระดับเซลล์แบบใช้ออกซิเจน (Aerobic respiration) ของกลูโคส 1 โมเลกุล แบ่งเป็น 4 ขั้นตอน:\n"
            "  1. ไกลโคไลซิส (Glycolysis): เกิดที่ไซโทซอล เปลี่ยนกลูโคส (6C) เป็นไพรูเวต (3C) 2 โมเลกุล ได้สุทธิ 2 ATP และ 2 NADH\n"
            "  2. การสร้างอะซิทิลโคเอนไซม์ เอ (Acetyl-CoA formation): เกิดที่เมทริกซ์ของไมโทคอนเดรีย ปล่อย CO2 และได้ 2 NADH\n"
            "  3. วัฏจักรเครบส์ (Krebs cycle / Citric acid cycle): เกิดที่เมทริกซ์ของไมโทคอนเดรีย ปล่อย CO2 ได้ 2 ATP (หรือ GTP), 6 NADH และ 2 FADH2\n"
            "  4. ลูกโซ่การถ่ายทอดอิเล็กตรอน (Electron transport chain - ETC): เกิดที่เยื่อหุ้มชั้นในของไมโทคอนเดรีย (Cristae) โดยมีออกซิเจน (O2) เป็นตัวรับอิเล็กตรอนตัวสุดท้ายรวมกับโปรตอนเกิดเป็นน้ำ (H2O) สร้างพลังงานรวมทั้งหมดประมาณ 30-32 ATP (หรือตามทฤษฎีดั้งเดิม 36-38 ATP)"
        ),
        'exam_tip': "ข้อสอบชอบถามสถานที่เกิดปฏิกิริยาและตัวรับอิเล็กตรอนตัวสุดท้าย: ไกลโคไลซิสเกิดที่ไซโทซอล (ไม่ใช้ O2) ส่วนตัวรับอิเล็กตรอนตัวสุดท้ายของ ETC คือ ออกซิเจน (O2) ซึ่งเมื่อรับแล้วจะกลายเป็นน้ำ (H2O)",
        'mnemonic': "สถานที่หายใจระดับเซลล์: 'ไกล-ไซ (ไกลโคไลซิส = ไซโทซอล) / เครบส์-เมท (วัฏจักรเครบส์ = เมทริกซ์) / อีทีซี-เยื่อใน (ETC = เยื่อหุ้มชั้นในไมโทคอนเดรีย)'",
    },
    {
        'id': 'bio-core-photosynthesis-genetics',
        'title': 'การสังเคราะห์ด้วยแสง และพันธุศาสตร์พื้นฐาน (Photosynthesis & Genetics)',
        'badge': 'หลักสูตรชีววิทยา ม.4-ม.5',
        'keywords': ['สังเคราะห์ด้วยแสง', 'ปฏิกิริยาแสง', 'วัฏจักรคัลวิน', 'คลอโรฟิลล์', 'พืช c3', 'พืช c4', 'พืช cam', 'พันธุศาสตร์', 'เมนเดล', 'ดีเอ็นเอ', 'อาร์เอ็นเอ', 'dna', 'rna', 'การจำลองดีเอ็นเอ', 'ถอดรหัส', 'แปลรหัส', 'ยีน', 'แอลลีล'],
        'content': (
            "• การสังเคราะห์ด้วยแสง (Photosynthesis) ในคลอโรพลาสต์ แบ่งเป็น 2 ขั้นตอนหลัก:\n"
            "  1. ปฏิกิริยาแสง (Light reaction): เกิดที่เยื่อไทลาคอยด์ (Thylakoid membrane) ใช้พลังงานแสงแตกตัวโมเลกุลน้ำ (Photolysis) ได้แก๊สออกซิเจน (O2) และสร้าง ATP กับ NADPH\n"
            "  2. การตรึงคาร์บอน / วัฏจักรคัลวิน (Calvin cycle): เกิดที่สโตรมา (Stroma) ใช้ ATP และ NADPH จากปฏิกิริยาแสงมาเปลี่ยน CO2 ให้เป็นน้ำตาล (G3P)\n"
            "  (ในพืช C3 สารตัวแรกที่เสถียรคือ PGA 3 คาร์บอน โดยมีเอนไซม์ RuBisCO ตรึง CO2 ส่วนพืช C4 เช่น ข้าวโพด อ้อย ข้าวฟ่าง ตรึง CO2 ครั้งแรกที่เซลล์มีโซฟิลล์ด้วยเอนไซม์ PEP carboxylase ได้ OAA 4 คาร์บอน ช่วยลดการหายใจแสง Photorespiration)\n\n"
            "• พันธุศาสตร์และอณูชีววิทยา (Genetics & Molecular Biology):\n"
            "  - กฎของเมนเดล: กฎแห่งการแยก (Law of Segregation) และกฎแห่งการรวมกลุ่มอย่างอิสระ (Law of Independent Assortment)\n"
            "  - Central Dogma: การจำลองตัวเองของ DNA (DNA Replication) -> การถอดรหัส (Transcription สร้าง mRNA จากแม่แบบ DNA) -> การแปลรหัส (Translation ที่ไรโบโซม แปลรหัสพันธุกรรม Codon บน mRNA เป็นสายพอลิเพปไทด์/โปรตีน)"
        ),
        'exam_tip': "แก๊สออกซิเจน (O2) ที่ได้จากการสังเคราะห์ด้วยแสง มาจากการแตกตัวของโมเลกุลน้ำ (H2O) ในปฏิกิริยาแสงที่ไทลาคอยด์ ไม่ได้มาจากแก๊สคาร์บอนไดออกไซด์ (CO2)!",
        'mnemonic': "สังเคราะห์ด้วยแสง: 'แสง-ไท-น้ำแตกได้ O2' (Light reaction ที่ Thylakoid) / 'คัลวิน-สโตรมา-ตรึง CO2 ได้น้ำตาล'",
    },
]


def _char_ngrams(text, n=RAG_NGRAM_SIZE):
    cleaned = re.sub(r'\s+', '', (text or '').lower())
    if len(cleaned) < n:
        return {cleaned} if cleaned else set()
    return {cleaned[i:i + n] for i in range(len(cleaned) - n + 1)}


def _similarity_score(question_grams, text):
    text_grams = _char_ngrams(text)
    if not question_grams or not text_grams:
        return 0.0
    overlap = len(question_grams & text_grams)
    if overlap < RAG_MIN_OVERLAP:
        return 0.0
    return overlap / len(question_grams)


def _split_into_chunks(text, max_chars=900):
    """แบ่งข้อความยาวๆ (จากบทเรียนหรือ PDF) ออกเป็นก้อนย่อยตามย่อหน้า เพื่อให้ RAG ดึงเฉพาะส่วนที่ตรงกับคำถามที่สุด"""
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        return [text[:max_chars]]

    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= max_chars:
                current = para
            else:
                for idx in range(0, len(para), max_chars):
                    chunks.append(para[idx:idx + max_chars])
                current = ""
    if current:
        chunks.append(current)
    return chunks


def _iter_knowledge_sources(exclude_lesson_pk=None):
    """ไล่คืนแหล่งข้อมูลทั้งหมดที่ใช้เป็นคลังค้นหาสำหรับ RAG จากข้อมูลจำลองในหน่วยความจำ (Database-free)"""
    from .mock_data import get_mock_lessons

    lessons_list = [l for l in get_mock_lessons(subject='bio') if l.pk != exclude_lesson_pk]
    for lesson_obj in lessons_list:
        text = f"{lesson_obj.title} {lesson_obj.description} {lesson_obj.content}"
        yield (f"บทเรียนที่เกี่ยวข้องในระบบ: {lesson_obj.title}", text)


def _retrieve_relevant_context(question, exclude_lesson_pk=None, top_k=RAG_TOP_K):
    """ค้นหาบทเรียน/เอกสารอ้างอิงที่เนื้อหาใกล้เคียงกับคำถามมากที่สุด คืนเป็นลิสต์ของ (label, text)"""
    sources = retrieve_biology_sources(question, exclude_lesson_pk=exclude_lesson_pk, top_k=top_k)
    return [(s['label'], s['full_text']) for s in sources]


def retrieve_biology_sources(query_text, focus_lesson=None, exclude_lesson_pk=None, top_k=RAG_TOP_K):
    """ค้นหาแหล่งความรู้ชีววิทยาที่ตรงกับคำถามมากที่สุดจากคลังบทเรียน Mockup และคลังความรู้หลักสูตรชีววิทยา"""
    from .mock_data import get_mock_lessons

    cleaned_query = (query_text or "").strip().lower()
    question_grams = _char_ngrams(cleaned_query)

    results = []

    # 📌 1. ถ้าผู้ใช้เลือกโฟกัสบทเรียนชีววิทยาไว้ ให้แนบบทเรียนนั้นเป็นแหล่งอ้างอิงอันดับแรกเสมอ
    if focus_lesson is not None and getattr(focus_lesson, 'subject', 'bio') == 'bio':
        chunks = _split_into_chunks(focus_lesson.content or focus_lesson.description or "")
        best_chunk = focus_lesson.description or ""
        best_score = 0.85
        if chunks and question_grams:
            scored_chunks = sorted(
                ((_similarity_score(question_grams, c), c) for c in chunks),
                key=lambda pair: pair[0],
                reverse=True,
            )
            if scored_chunks[0][0] > 0:
                best_chunk = scored_chunks[0][1]
                best_score = max(0.85, min(0.99, scored_chunks[0][0]))
            else:
                best_chunk = chunks[0]

        results.append({
            'type': 'lesson',
            'id': focus_lesson.pk,
            'title': focus_lesson.title,
            'badge': f"บทเรียน {focus_lesson.get_grade_display()} · บทที่ {focus_lesson.chapter}",
            'label': f"บทเรียนที่โฟกัส: {focus_lesson.title}",
            'snippet': best_chunk[:360] + ("…" if len(best_chunk) > 360 else ""),
            'full_text': f"{focus_lesson.title}\n{focus_lesson.description}\n{best_chunk}",
            'score_percent': int(round(best_score * 100)),
            'exam_tip': '',
            'mnemonic': '',
        })
        exclude_lesson_pk = focus_lesson.pk

    if not question_grams:
        return results[:top_k]

    scored_candidates = []

    # 📌 2. ค้นหาจากบทเรียนวิชาชีววิทยาทั้งหมดในหน่วยความจำ
    lessons_list = [l for l in get_mock_lessons(subject='bio') if l.pk != exclude_lesson_pk]

    for lesson_obj in lessons_list:
        header_text = f"{lesson_obj.title} {lesson_obj.chapter_title} {lesson_obj.description}"
        chunks = _split_into_chunks(lesson_obj.content) or [lesson_obj.description]
        best_chunk = chunks[0] if chunks else lesson_obj.description
        best_chunk_score = _similarity_score(question_grams, header_text)

        for chunk in chunks:
            c_score = _similarity_score(question_grams, f"{lesson_obj.title} {chunk}")
            if c_score > best_chunk_score:
                best_chunk_score = c_score
                best_chunk = chunk

        if lesson_obj.title and lesson_obj.title.lower() in cleaned_query:
            best_chunk_score = max(best_chunk_score, 0.75)

        if best_chunk_score >= RAG_MIN_SCORE:
            scored_candidates.append((
                best_chunk_score,
                {
                    'type': 'lesson',
                    'id': lesson_obj.pk,
                    'title': lesson_obj.title,
                    'badge': f"บทเรียน {lesson_obj.get_grade_display()} · บทที่ {lesson_obj.chapter}",
                    'label': f"บทเรียนที่เกี่ยวข้องในระบบ: {lesson_obj.title}",
                    'snippet': best_chunk[:360] + ("…" if len(best_chunk) > 360 else ""),
                    'full_text': f"{lesson_obj.title} ({lesson_obj.get_grade_display()})\n{lesson_obj.description}\n{best_chunk}",
                    'score_percent': min(99, max(20, int(round(best_chunk_score * 100)))),
                    'exam_tip': '',
                    'mnemonic': '',
                }
            ))

    # 📌 4. ค้นหาจากคลังความรู้หลักสูตรชีววิทยา ม.ปลาย ในตัว (BIOLOGY_CORE_KNOWLEDGE)
    for item in BIOLOGY_CORE_KNOWLEDGE:
        keyword_hits = sum(1 for kw in item['keywords'] if kw.lower() in cleaned_query)
        ngram_score = _similarity_score(question_grams, f"{item['title']} {' '.join(item['keywords'])} {item['content']}")
        combined_score = max(ngram_score, min(0.95, keyword_hits * 0.28))
        if combined_score >= RAG_MIN_SCORE:
            scored_candidates.append((
                combined_score,
                {
                    'type': 'curriculum',
                    'id': item['id'],
                    'title': item['title'],
                    'badge': item['badge'],
                    'label': f"คลังความรู้หลักสูตรชีววิทยา: {item['title']}",
                    'snippet': item['content'][:360] + ("…" if len(item['content']) > 360 else ""),
                    'full_text': item['content'],
                    'score_percent': min(99, max(25, int(round(combined_score * 100)))),
                    'exam_tip': item.get('exam_tip', ''),
                    'mnemonic': item.get('mnemonic', ''),
                }
            ))

    scored_candidates.sort(key=lambda pair: pair[0], reverse=True)
    for _, source_dict in scored_candidates:
        if len(results) >= top_k:
            break
        results.append(source_dict)

    return results


def extract_pdf_text(file_path, max_chars=200000):
    """แกะข้อความจากไฟล์ PDF ด้วยไลบรารี pypdf คืนเป็น string"""
    try:
        import pypdf
    except ImportError:
        raise AskAIError("ยังไม่ได้ติดตั้งไลบรารี pypdf — รันคำสั่ง: pip install pypdf")

    try:
        reader = pypdf.PdfReader(file_path)
        pages_text = [(page.extract_text() or "") for page in reader.pages]
        return "\n\n".join(pages_text).strip()[:max_chars]
    except Exception as exc:
        raise AskAIError(f"แกะข้อความจากไฟล์ PDF ไม่สำเร็จ: {exc}")


def _synthesize_local_biology_response(question, sources, history=None, tutor_mode='explain'):
    """สังเคราะห์คำตอบวิชาชีววิทยาจากคลังความรู้ RAG ในระบบ (ใช้เมื่อยังไม่ได้ตั้งค่า ANTHROPIC_API_KEY)
    รองรับการจำบริบทบทสนทนาก่อนหน้า และปรับรูปแบบการสอนตาม tutor_mode"""
    q_lower = question.lower()

    # 📌 ตรวจสอบคำถามนอกเรื่องชีววิทยา
    if any(kw in q_lower for kw in NON_BIO_KEYWORDS):
        return (
            "ขออภัยครับ ผมเป็น **ติวเตอร์ AI เฉพาะทางวิชาชีววิทยา** 🧬 จึงสามารถตอบได้เฉพาะเรื่องที่เกี่ยวกับชีววิทยา "
            "เซลล์ พันธุศาสตร์ ระบบร่างกาย พืช และวิทยาศาสตร์ชีวภาพระดับมัธยมปลายเท่านั้นครับ\n\n"
            "ลองถามคำถามชีววิทยา เช่น *\"เซลล์พืชกับเซลล์สัตว์ต่างกันอย่างไร?\"* หรือ *\"ไมโทซิสกับไมโอซิสต่างกันตรงไหน?\"* ได้เลยครับ!"
        )

    # 📌 ถ้าไม่พบแหล่งอ้างอิงจากคำถามปัจจุบันโดยตรง แต่มีบทสนทนาก่อนหน้า ให้ดึงบริบทจากคำถามก่อนหน้ามาช่วย
    if not sources and history:
        prev_topics = [msg.get('content', '') for msg in history if msg.get('role') == 'user']
        if prev_topics:
            combined_query = f"{prev_topics[-1]} {question}"
            sources = retrieve_biology_sources(combined_query, top_k=3)

    if not sources:
        # ดึงหัวข้อบทเรียนชีววิทยาในระบบมาแนะนำ
        from .mock_data import get_mock_lessons
        sample_titles = [l.title for l in get_mock_lessons(subject='bio')[:5]]
        sample_str = " / ".join(sample_titles) if sample_titles else "เซลล์ของสิ่งมีชีวิต / การแบ่งเซลล์ / การลำเลียงสาร"
        return (
            f"คำถามน่าสนใจมากครับ! เพื่อให้ผมดึงเนื้อหาจากคลังความรู้ชีววิทยามาอธิบายได้ตรงจุดที่สุด "
            f"คุณสามารถระบุคำสำคัญทางชีววิทยาเพิ่มเติม หรือเลือกถามในหัวข้อที่มีในระบบ เช่น:\n"
            f"• {sample_str}\n"
            f"• โครงสร้างและหน้าที่ของออร์แกเนลล์ภายในเซลล์\n"
            f"• การหายใจระดับเซลล์ และการสังเคราะห์ด้วยแสง\n"
            f"• พันธุศาสตร์เมนเดล และสารพันธุกรรม (DNA/RNA)"
        )

    primary = sources[0]
    supporting = sources[1:3]

    mode_headers = {
        'explain': f"📖 **อธิบายความรู้ชีววิทยา: {primary['title']}**",
        'exam_prep': f"🎯 **สรุปติวเข้ม & จุดออกสอบ: {primary['title']}**",
        'socratic': f"🧠 **ชวนคิดวิเคราะห์ทางชีววิทยา: {primary['title']}**",
        'summary': f"⚡ **สรุปย่อ & เทคนิคช่วยจำ: {primary['title']}**",
    }
    header = mode_headers.get(tutor_mode, mode_headers['explain'])

    parts = [header]

    if history and len(history) >= 2:
        parts.append("*(อ้างอิงต่อเนื่องจากบทสนทนาก่อนหน้าของคุณ)*")

    # เนื้อหาหลักที่ดึงมาจากบทเรียน/เอกสาร PDF/หลักสูตรชีววิทยา
    parts.append(primary['full_text'].strip())

    if supporting:
        extra_points = []
        for sup in supporting:
            snippet_clean = sup['snippet'].replace('\n', ' ').strip()
            extra_points.append(f"• **{sup['title']} ({sup['badge']})**: {snippet_clean}")
        parts.append("🔗 **ความรู้ชีววิทยาที่เชื่อมโยงกัน:**\n" + "\n".join(extra_points))

    # ปรับส่วนท้ายตามโหมดการสอน (tutor_mode)
    exam_tip = primary.get('exam_tip') or next((s.get('exam_tip') for s in sources if s.get('exam_tip')), '')
    mnemonic = primary.get('mnemonic') or next((s.get('mnemonic') for s in sources if s.get('mnemonic')), '')

    if tutor_mode == 'exam_prep':
        if exam_tip:
            parts.append(f"⚠️ **จุดเน้นข้อสอบ ม.ปลาย / A-Level:**\n{exam_tip}")
        else:
            parts.append(
                "⚠️ **เทคนิคทำข้อสอบชีววิทยาเรื่องนี้:**\n"
                "เวลาเจอโจทย์เปรียบเทียบ ให้ขีดเส้นใต้คำสำคัญว่าเป็นระดับ *เซลล์*, *เนื้อเยื่อ* หรือ *อวัยวะ* "
                "และตรวจสอบเงื่อนไขของตัวแปรต้น-ตัวแปรตามให้แม่นยำ"
            )
    elif tutor_mode == 'socratic':
        parts.append(
            f"🤔 **คำถามชวนคิดต่อ (ลองตอบดูนะครับ!):**\n"
            f"จากหลักการของ **{primary['title']}** ข้างต้น ถ้าเกิดการเปลี่ยนแปลงของสภาพแวดล้อมหรือโครงสร้างส่วนนี้ทำงานผิดปกติไป "
            f"คุณคิดว่าผลกระทบแรกที่จะเกิดขึ้นกับสิ่งมีชีวิตคืออะไร? ลองพิมพ์คำตอบมาคุยกันต่อได้เลย!"
        )
    elif tutor_mode == 'summary':
        if mnemonic:
            parts.append(f"💡 **เทคนิคช่วยจำ (Mnemonic):**\n{mnemonic}")
        else:
            parts.append(
                f"💡 **เทคนิคช่วยจำเร็ว:**\n"
                f"สรุปแก่นของ **{primary['title']}** ให้จำ 3 คำถามหลัก: *เกิดขึ้นที่ไหน (Location)* -> *ทำหน้าที่อะไร (Function)* -> *ผลลัพธ์ที่ได้คืออะไร (Output)*"
            )
    else:
        if mnemonic or exam_tip:
            extra_tip = mnemonic or exam_tip
            parts.append(f"💡 **เกร็ดความรู้เสริม:** {extra_tip}")

    return "\n\n".join(parts)


def ask_biology_tutor_chat(question, history=None, lesson=None, tutor_mode='explain'):
    """ฟังก์ชันหลักสำหรับ 'แชทบอทติวเตอร์ชีววิทยาอัจฉริยะ'
    - รองรับการจำบทสนทนาต่อเนื่อง (history เป็น list ของ {'role': 'user'|'assistant', 'content': str})
    - รองรับการเลือกโหมดติวเตอร์ (tutor_mode: explain, exam_prep, socratic, summary)
    - ค้นหาแหล่งอ้างอิงจากบทเรียนชีววิทยา + PDF + คลังหลักสูตรชีววิทยา (RAG) พร้อมคืนรายการแหล่งอ้างอิง (sources)
    - หากตั้งค่า ANTHROPIC_API_KEY จะเรียก Claude API พร้อมประวัติการสนทนา
    - หากยังไม่ได้ตั้งค่า ANTHROPIC_API_KEY จะใช้ Local Biology RAG Engine ตอบจากคลังความรู้ในระบบทันที
    """
    question = (question or "").strip()
    if not question:
        raise AskAIError("กรุณาพิมพ์คำถามชีววิทยาก่อนส่ง")
    if len(question) > MAX_QUESTION_LENGTH:
        raise AskAIError(f"คำถามยาวเกินไป (จำกัดไม่เกิน {MAX_QUESTION_LENGTH} ตัวอักษร)")

    history = list(history or [])[-MAX_HISTORY_TURNS:]

    # 📌 รวมบริบทคำถามปัจจุบันกับคำถามล่าสุดในห้องแชท เพื่อให้การค้นหา RAG แม่นยำแม้ถามสั้นๆ ต่อเนื่อง (เช่น "แล้วต่างกันยังไง?")
    rag_query = question
    recent_user_msgs = [m.get('content', '') for m in history if m.get('role') == 'user']
    if len(question) < 45 and recent_user_msgs:
        rag_query = f"{recent_user_msgs[-1]} {question}"

    sources = retrieve_biology_sources(rag_query, focus_lesson=lesson, top_k=RAG_TOP_K)

    # 📌 สร้างรายการ sources สำหรับเก็บลง JSONField และแสดงผลการ์ดอ้างอิงบนหน้าเว็บ
    public_sources = [
        {
            'type': s['type'],
            'id': s['id'],
            'title': s['title'],
            'badge': s['badge'],
            'snippet': s['snippet'],
            'score_percent': s['score_percent'],
        }
        for s in sources
    ]

    # 📌 กรณีมี ANTHROPIC_API_KEY: เรียกใช้งาน Claude API แบบ Multi-turn Chat + RAG
    if getattr(settings, 'ANTHROPIC_API_KEY', ''):
        try:
            import anthropic
            mode_instruction = TUTOR_MODE_INSTRUCTIONS.get(tutor_mode, TUTOR_MODE_INSTRUCTIONS['explain'])
            full_system_prompt = (
                f"{SYSTEM_PROMPT}\n\n{mode_instruction}\n"
                "เมื่อใช้ข้อมูลจากบริบทที่แนบไป ให้กล่าวอ้างอิงชื่อบทเรียนหรือเอกสารประกอบด้วยเพื่อให้ผู้เรียนตามไปอ่านต่อได้"
            )

            context_blocks = [
                f"[{s['label']} ({s['badge']})]\n{s['full_text'][:RAG_CHUNK_CHARS]}"
                for s in sources
            ]
            augmented_user_content = question
            if context_blocks:
                joined_context = "\n\n".join(context_blocks)
                augmented_user_content = (
                    f"บริบทเนื้อหาชีววิทยาจากระบบที่เกี่ยวข้องกับคำถาม:\n\n{joined_context}\n\n"
                    f"คำถามของผู้เรียน: {question}"
                )

            api_messages = []
            for turn in history:
                role = turn.get('role')
                content = (turn.get('content') or '').strip()
                if role in ('user', 'assistant') and content:
                    if not api_messages or api_messages[-1]['role'] != role:
                        api_messages.append({'role': role, 'content': content})

            if api_messages and api_messages[-1]['role'] == 'user':
                api_messages[-1]['content'] = f"{api_messages[-1]['content']}\n\n{augmented_user_content}"
            else:
                api_messages.append({'role': 'user', 'content': augmented_user_content})

            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1024,
                system=full_system_prompt,
                messages=api_messages,
            )
            answer_text = "".join(block.text for block in response.content if hasattr(block, "text")).strip()
            return {
                'answer': answer_text,
                'sources': public_sources,
                'engine': 'claude',
            }
        except Exception as exc:
            raise AskAIError(f"เรียก AI ไม่สำเร็จ: {exc}")

    # 📌 กรณียังไม่ได้ตั้งค่า ANTHROPIC_API_KEY: ใช้ Local Biology Knowledge RAG Engine ตอบทันที
    answer_text = _synthesize_local_biology_response(
        question=question,
        sources=sources,
        history=history,
        tutor_mode=tutor_mode,
    )
    return {
        'answer': answer_text,
        'sources': public_sources,
        'engine': 'local_bio_rag',
    }


def ask_biology_ai(question, lesson=None):
    """ส่งคำถามไปถาม AI วิชาชีววิทยาแล้วคืนคำตอบเป็นข้อความ (string)
    คงฟังก์ชันนี้ไว้เพื่อให้ส่วนกล่องถามเร็วในหน้าบทเรียน (lesson_detail) และโค้ดเดิมเรียกใช้งานได้ตามปกติ"""
    result = ask_biology_tutor_chat(question, history=None, lesson=lesson, tutor_mode='explain')
    return result['answer']
