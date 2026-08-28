import pymysql
pymysql.install_as_MySQLdb()

# ข้ามการเช็กเวอร์ชัน MariaDB
from django.db.backends.mysql.base import DatabaseWrapper
DatabaseWrapper.check_database_version_supported = lambda self: None

# ปิดการใช้ฟีเจอร์ RETURNING ที่ MariaDB 10.4 ไม่รองรับ
from django.db.backends.mysql.features import DatabaseFeatures
DatabaseFeatures.can_return_columns_from_insert = False