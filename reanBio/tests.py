from django.test import SimpleTestCase, Client
from django.urls import reverse


class ReanBioMockupTests(SimpleTestCase):
    """ชุดทดสอบโหมด Mockup (ไม่ใช้ฐานข้อมูล — SimpleTestCase)"""

    def setUp(self):
        self.client = Client()

    def test_home_and_role_switcher_buttons(self):
        """หน้าหลักและปุ่มสลับบทบาท นักเรียน/คุณครู/ผู้เยี่ยมชม ทำงานได้โดยไม่ต้องสมัครสมาชิกจริง"""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'โหมด Mockup:')

        # กดปุ่มสลับเป็นคุณครู
        resp_teacher = self.client.get(reverse('login') + '?role=teacher', follow=True)
        self.assertEqual(resp_teacher.status_code, 200)
        self.assertContains(resp_teacher, 'แดชบอร์ดจัดการห้องเรียน')

        # กดปุ่มสลับเป็นนักเรียน
        resp_student = self.client.get(reverse('signup') + '?role=student', follow=True)
        self.assertEqual(resp_student.status_code, 200)

    def test_lessons_and_flashcards_without_db(self):
        """คลังบทเรียนและการ์ดคำศัพท์แสดงผลจากข้อมูลจำลองในหน่วยความจำได้ครบถ้วน"""
        resp_lessons = self.client.get(reverse('lessons'))
        self.assertEqual(resp_lessons.status_code, 200)
        self.assertContains(resp_lessons, 'คลังบทเรียนชีววิทยา')

        resp_fc = self.client.get(reverse('flashcards'))
        self.assertEqual(resp_fc.status_code, 200)
        self.assertContains(resp_fc, 'การ์ดคำศัพท์')

    def test_biology_ai_tutor_mockup_chat(self):
        """แชทบอทติวเตอร์ AI ชีววิทยาสามารถตอบคำถามต่อเนื่องพร้อมแสดงแหล่งอ้างอิงได้โดยไม่ใช้ฐานข้อมูล"""
        ask_url = reverse('ask_ai')
        resp = self.client.post(ask_url, {
            'ai_question': 'ไมโทซิสกับไมโอซิสต่างกันอย่างไร?',
            'tutor_mode': 'exam_prep',
            'lesson_id': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'ไมโทซิส')
        self.assertContains(resp, 'แหล่งอ้างอิงความรู้ชีววิทยาที่ใช้ประกอบการตอบ')
