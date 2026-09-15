from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class UserSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="อีเมล")
    first_name = forms.CharField(max_length=50, required=False, label="ชื่อจริง")
    last_name = forms.CharField(max_length=50, required=False, label="นามสกุล")
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='student', label="บทบาท")

    # 📌 บังคับให้กรอกอีเมลเสมอ (ใช้สำหรับ "ลืมรหัสผ่าน") + คุมลำดับการแสดงผลของช่องกรอกในฟอร์ม
    field_order = ['email', 'username', 'password1', 'password2', 'role', 'first_name', 'last_name']

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("อีเมลนี้มีผู้ใช้งานแล้ว กรุณาใช้อีเมลอื่น หรือเข้าสู่ระบบแทน")
        return email


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    """เหมือน AuthenticationForm ของ Django ทุกอย่าง แค่เปลี่ยนข้อความ error ให้เป็นภาษาไทย
    (ตัวระบบเข้าสู่ระบบด้วย username หรืออีเมลจริงๆ อยู่ที่ EmailOrUsernameModelBackend)"""
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': "เข้าสู่ระบบไม่สำเร็จ กรุณาตรวจสอบ Username/อีเมล และรหัสผ่านอีกครั้ง",
        'inactive': "บัญชีนี้ถูกระงับการใช้งาน",
    }
