from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import UserProfile, Classroom, Lesson
from .forms import UserSignUpForm

# 📌 Decorator เช็กสิทธิ์เฉพาะคุณครู
def teacher_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if getattr(request.user, 'is_teacher', False):
            return view_func(request, *args, **kwargs)
        return redirect('my_classrooms')
    return _wrapped_view

def home(request):
    return render(request, 'index.html')

def signup(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data.get('role')
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.save()

            user_grade = request.POST.get('grade_level', request.POST.get('grade', '')).strip()
            UserProfile.objects.create(
                user=user,
                grade=user_grade
            )

            login(request, user)
            if getattr(user, 'is_teacher', False):
                return redirect('teacher_dashboard')
            return redirect('home')
    else:
        form = UserSignUpForm()

    return render(request, 'reanBio/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # 🛑 บล็อกบัญชี Admin ไม่ให้ล็อกอินผ่านหน้าเว็บปกติ
            if user.is_superuser or user.is_staff:
                form.add_error(None, 'บัญชีผู้ดูแลระบบ (Admin) ไม่สามารถเข้าใช้งานหน้านี้ได้ กรุณาเข้าสู่ระบบผ่านหน้า /admin/')
            else:
                login(request, user)
                if getattr(user, 'is_teacher', False):
                    return redirect('teacher_dashboard')
                return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'reanBio/login.html', {'form': form})

def lessons_view(request):
    grade_filter = request.GET.get('grade', 'all')
    search_query = request.GET.get('q', '').strip()

    lessons = Lesson.objects.all()

    if grade_filter in ['m4', 'm5', 'm6']:
        lessons = lessons.filter(grade=grade_filter)

    if search_query:
        lessons = lessons.filter(title__icontains=search_query)

    return render(request, 'reanBio/lessons.html', {
        'lessons': lessons,
        'current_grade': grade_filter,
        'search_query': search_query,
    })

@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    return render(request, 'reanBio/profile.html', {'profile': user_profile})

def user_logout(request):
    logout(request)
    return redirect('home')

# 📌 แดชบอร์ดจัดการห้องเรียนของคุณครู
@teacher_required
def teacher_dashboard_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Classroom.objects.create(name=name, teacher=request.user)
            messages.success(request, 'สร้างห้องเรียนสำเร็จ!')
            return redirect('teacher_dashboard')

    classrooms = Classroom.objects.filter(teacher=request.user).order_by('-created_at')
    return render(request, 'reanBio/teacher_dashboard.html', {'classrooms': classrooms})

# 📌 หน้าห้องเรียนของฉัน (สำหรับนักเรียน)
@login_required
def my_classroom_view(request):
    joined_classrooms = request.user.joined_classrooms.all().order_by('-created_at')
    return render(request, 'reanBio/my_classrooms.html', {'classrooms': joined_classrooms})

# 📌 ฟังก์ชันให้นักเรียนกรอกรหัสเข้าร่วมห้องเรียน
@login_required
def join_classroom_view(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        try:
            classroom = Classroom.objects.get(code=code)
            classroom.students.add(request.user)
            messages.success(request, f'เข้าร่วมห้องเรียน "{classroom.name}" เรียบร้อยแล้ว!')
            return redirect('classroom_detail', code=classroom.code)
        except Classroom.DoesNotExist:
            messages.error(request, 'ไม่พบห้องเรียนรหัสนี้ กรุณาตรวจสอบรหัสอีกครั้ง')
            return redirect('my_classrooms')
    return redirect('my_classrooms')

# 📌 รายละเอียดภายในห้องเรียน
@login_required
def classroom_detail_view(request, code):
    classroom = get_object_or_404(Classroom, code=code)
    return render(request, 'reanBio/classroom_detail.html', {'classroom': classroom})

@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    # แยกการดึงข้อมูลห้องเรียนตามบทบาทผู้ใช้
    if getattr(request.user, 'is_teacher', False):
        classrooms = Classroom.objects.filter(teacher=request.user).order_by('-created_at')
    else:
        classrooms = request.user.joined_classrooms.all().order_by('-created_at')

    return render(request, 'reanBio/profile.html', {
        'profile': user_profile,
        'classrooms': classrooms
    })

@login_required
def my_classroom_view(request):
    # 🛑 ถ้าเป็นคุณครู ให้เด้งไปหน้าแดชบอร์ดสร้าง/จัดการห้องเรียนทันที
    if getattr(request.user, 'is_teacher', False):
        return redirect('teacher_dashboard')

    joined_classrooms = request.user.joined_classrooms.all().order_by('-created_at')
    return render(request, 'reanBio/my_classrooms.html', {'classrooms': joined_classrooms})

def lesson_detail_view(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    return render(request, 'reanBio/lesson_detail.html', {'lesson': lesson})