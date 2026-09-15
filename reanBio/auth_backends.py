# 📌 ตัวช่วยให้เข้าสู่ระบบได้ทั้งด้วย username หรืออีเมล (กรอกช่องเดียวกัน ระบบจะเดาให้เอง)
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameModelBackend(ModelBackend):
    """เหมือน ModelBackend ของ Django ทุกอย่าง ยกเว้นตอนหา user จะลองด้วย username ก่อน
    ถ้าไม่เจอและดูเหมือนเป็นอีเมล (มี @) จะลองหาด้วยอีเมลแทน"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        user = UserModel._default_manager.filter(username__iexact=username).first()
        if user is None and '@' in username:
            # 📌 ถ้ามีหลายบัญชีใช้อีเมลเดียวกันโดยบังเอิญ (ข้อมูลเก่าก่อนบังคับอีเมลไม่ซ้ำ) จะไม่เดาว่าเป็นใคร กันเข้าระบบผิดคน
            candidates = list(UserModel._default_manager.filter(email__iexact=username)[:2])
            if len(candidates) == 1:
                user = candidates[0]

        if user is None:
            # 📌 รัน hash เปล่าๆ ให้เวลาตอบสนองใกล้เคียงกรณีเจอ user จริง กันการเดาจากเวลาตอบสนอง (timing attack)
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
