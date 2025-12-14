import sys
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QComboBox, QLineEdit, QLabel, 
                            QTableWidget, QTableWidgetItem, QTextEdit, QMessageBox,
                            QTabWidget, QFrame, QScrollArea, QGroupBox, QSpinBox,
                            QFileDialog, QDialog, QDialogButtonBox, QFormLayout,
                            QCheckBox)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QPixmap, QPainter

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                policy_number TEXT NOT NULL,
                policy_date TEXT NOT NULL,
                total_value INTEGER NOT NULL,
                remaining_value INTEGER NOT NULL,
                FOREIGN KEY (company_name) REFERENCES companies(name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sanad_id INTEGER NOT NULL,
                sanad_date TEXT NOT NULL,
                company_name TEXT NOT NULL,
                policy_id INTEGER NOT NULL,
                policy_number TEXT NOT NULL,
                policy_date TEXT NOT NULL,
                cottage_numbers TEXT NOT NULL,
                count INTEGER NOT NULL,
                value INTEGER NOT NULL,
                remaining_after INTEGER NOT NULL,
                FOREIGN KEY (company_name) REFERENCES companies(name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_next_sanad_id(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(sanad_id) FROM certificates')
        result = cursor.fetchone()[0]
        next_id = (result or 3999) + 1
        conn.close()
        return next_id

    def add_company(self, name):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO companies (name) VALUES (?)', (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_companies(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM companies ORDER BY name')
        companies = [row[0] for row in cursor.fetchall()]
        conn.close()
        return companies

    def add_policy(self, company_name, policy_number, policy_date, total_value):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO policies (company_name, policy_number, policy_date, total_value, remaining_value)
                VALUES (?, ?, ?, ?, ?)
            ''', (company_name, policy_number, policy_date, total_value, total_value))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_policies(self, company_name=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if company_name:
            cursor.execute('''
                SELECT id, policy_number, policy_date, total_value, remaining_value 
                FROM policies WHERE company_name = ? AND remaining_value > 0
                ORDER BY policy_number
            ''', (company_name,))
        else:
            cursor.execute('SELECT id, company_name, policy_number, policy_date, total_value, remaining_value FROM policies ORDER BY company_name, policy_number')
        policies = cursor.fetchall()
        conn.close()
        return policies

    def check_cottage_exists(self, cottage_numbers):
        if not cottage_numbers:
            return []
        cottages = [c.strip() for c in cottage_numbers.split('-')]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(cottages))
        query = f'SELECT sanad_id FROM certificates WHERE cottage_numbers LIKE "%{cottage_numbers}%" OR cottage_numbers LIKE "%{cottage_numbers.split("-")[0]}%"'
        cursor.execute(query)
        existing = cursor.fetchall()
        conn.close()
        return [row[0] for row in existing]

    def add_certificate(self, sanad_id, sanad_date, company_name, policy_id, policy_number, policy_date, cottage_numbers, count, value):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        remaining_after = 0
        
        cursor.execute('SELECT remaining_value FROM policies WHERE id = ?', (policy_id,))
        current_remaining = cursor.fetchone()[0]
        
        if value > current_remaining:
            conn.close()
            return False, 0
        
        remaining_after = current_remaining - value
        
        cursor.execute('''
            UPDATE policies SET remaining_value = remaining_value - ? WHERE id = ?
        ''', (value, policy_id))
        
        cursor.execute('''
            INSERT INTO certificates (sanad_id, sanad_date, company_name, policy_id, policy_number, policy_date, cottage_numbers, count, value, remaining_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sanad_id, sanad_date, company_name, policy_id, policy_number, policy_date, cottage_numbers, count, value, remaining_after))
        
        conn.commit()
        conn.close()
        return True, remaining_after

class CertificatePrintDialog(QDialog):
    def __init__(self, certificate_data, parent=None):
        super().__init__(parent)
        self.certificate_data = certificate_data
        self.setWindowTitle("پیش‌نمایش گواهی")
        self.setModal(True)
        self.setFixedSize(600, 800)
        layout = QVBoxLayout(self)
        
        print_area = QTextEdit()
        print_area.setReadOnly(True)
        print_area.setHtml(self.generate_certificate_html(certificate_data))
        layout.addWidget(print_area)
        
        button_layout = QHBoxLayout()
        print_button = QPushButton("چاپ")
        print_button.clicked.connect(lambda: print_area.print_())
        close_button = QPushButton("بستن")
        close_button.clicked.connect(self.reject)
        
        button_layout.addWidget(print_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def generate_certificate_html(self, data):
        return f"""
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Tahoma, Arial, sans-serif; font-size: 14px; margin: 20px; }}
                .header {{ border-bottom: 3px solid black; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
                .info-box {{ border: 2px solid black; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .field {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
                .label {{ font-weight: bold; width: 120px; }}
                .value {{ text-align: right; }}
                .footer {{ margin-top: 30px; text-align: center; }}
                .signature-area {{ margin-top: 40px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div style="text-align: center; flex: 1;">
                    <h2>بیمه سینا</h2>
                    <h3>گواهی حمل بار داخلی/وارداتی</h3>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 12px; margin-bottom: 5px;">نمایندگی سهرابی فرد</div>
                    <div style="font-size: 11px;">کد 6065</div>
                </div>
            </div>
            
            <div class="field">
                <div class="label">شماره سند:</div>
                <div class="value" style="font-family: Courier New; font-size: 16px;">{data['sanad_id']}</div>
            </div>
            <div class="field">
                <div class="label">تاریخ صدور:</div>
                <div class="value">{data['sanad_date']}</div>
            </div>
            
            <div class="info-box">
                <div class="field"><div class="label">نام شرکت:</div><div class="value">{data['company_name']}</div></div>
                <div class="field"><div class="label">شماره بیمه‌نامه:</div><div class="value">{data['policy_number']}</div></div>
                <div class="field"><div class="label">تاریخ بیمه‌نامه:</div><div class="value">{data['policy_date']}</div></div>
                <div class="field"><div class="label">ارزش کل بیمه:</div><div class="value">{data['total_value']:,} ریال</div></div>
            </div>
            
            <div class="info-box">
                <div class="field"><div class="label">مبدا و مقصد:</div><div class="value">امارات عربی / بندرلنگه</div></div>
                <div class="field"><div class="label">شماره کوتاژها:</div><div class="value">{data['cottage_numbers']}</div></div>
                <div class="field"><div class="label">تعداد:</div><div class="value">{data['count']}</div></div>
                <div class="field"><div class="label">ارزش محموله:</div><div class="value" style="font-weight: bold; font-size: 16px;">{data['value']:,} ریال</div></div>
            </div>
            
            <div style="background: #f0f0f0; padding: 15px; border: 2px solid black; border-radius: 5px; margin-top: 20px;">
                <div style="display: flex; justify-content: space-between; font-weight: bold;">
                    <span>مانده اعتبار بیمه‌نامه:</span>
                    <span>{data['remaining_after']:,} ریال</span>
                </div>
            </div>
            
            <div class="footer">
                <div class="signature-area">
                    <div style="text-align: center;">
                        <div>مهر و امضاء بیمه‌گر</div>
                    </div>
                </div>
                <div style="border-top: 1px solid black; padding-top: 10px; font-size: 12px; text-align: center;">
                    آدرس: بندرلنگه، مجتمع یاقوت، طبقه اول | تلفن: 09173621318
                </div>
            </div>
        </body>
        </html>
        """

class InsuranceSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager("insurance_system.db")
        self.current_language = "fa"
        self.languages = {
            "fa": {"name": "فارسی", "direction": Qt.LayoutDirection.RightToLeft},
            "en": {"name": "English", "direction": Qt.LayoutDirection.LeftToRight},
            "zh": {"name": "中文", "direction": Qt.LayoutDirection.LeftToRight},
            "ru": {"name": "Русский", "direction": Qt.LayoutDirection.LeftToRight}
        }
        
        self.init_ui()
        self.apply_language()

    def init_ui(self):
        self.setWindowTitle("سیستم صدور گواهی بیمه باربری")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # نوار کناری
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # انتخاب زبان
        language_group = QGroupBox("انتخاب زبان")
        language_layout = QHBoxLayout(language_group)
        self.language_combo = QComboBox()
        for code, info in self.languages.items():
            self.language_combo.addItem(info["name"], code)
        self.language_combo.currentTextChanged.connect(self.change_language)
        language_layout.addWidget(self.language_combo)
        sidebar_layout.addWidget(language_group)
        
        # انتخاب تم
        theme_group = QGroupBox("انتخاب تم")
        theme_layout = QHBoxLayout(theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["پیش‌فرض", "روشن", "تاریک", "آبی", "قرمز"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        sidebar_layout.addWidget(theme_group)
        
        # دکمه‌های ناوبری
        self.create_cert_btn = QPushButton("ثبت گواهی جدید")
        self.create_cert_btn.clicked.connect(lambda: self.show_tab(0))
        sidebar_layout.addWidget(self.create_cert_btn)
        
        self.new_policy_btn = QPushButton("ثبت بیمه‌نامه جدید")
        self.new_policy_btn.clicked.connect(lambda: self.show_tab(1))
        sidebar_layout.addWidget(self.new_policy_btn)
        
        self.companies_btn = QPushButton("مدیریت شرکت‌ها")
        self.companies_btn.clicked.connect(lambda: self.show_tab(2))
        sidebar_layout.addWidget(self.companies_btn)
        
        self.history_btn = QPushButton("سوابق اسناد")
        self.history_btn.clicked.connect(lambda: self.show_tab(3))
        sidebar_layout.addWidget(self.history_btn)
        
        self.report_btn = QPushButton("گزارش مانده بیمه‌نامه‌ها")
        self.report_btn.clicked.connect(lambda: self.show_tab(4))
        sidebar_layout.addWidget(self.report_btn)
        
        # دکمه‌های پشتیبان‌گیری
        backup_btn = QPushButton("پشتیبان‌گیری")
        backup_btn.clicked.connect(self.backup_database)
        sidebar_layout.addWidget(backup_btn)
        
        restore_btn = QPushButton("بازیابی پشتیبان")
        restore_btn.clicked.connect(self.restore_database)
        sidebar_layout.addWidget(restore_btn)
        
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)
        
        # محتوای اصلی
        self.main_content = QTabWidget()
        main_layout.addWidget(self.main_content, 1)
        
        # ایجاد تب‌ها
        self.setup_certificate_tab()
        self.setup_policy_tab()
        self.setup_companies_tab()
        self.setup_history_tab()
        self.setup_report_tab()
        
        # بارگذاری اولیه داده‌ها پس از ایجاد تمام کنترل‌ها
        self.refresh_all_company_combos()
        
        # به‌روزرسانی جداول
        self.update_companies_table()
        self.update_policies_table()
        
        # تنظیم تب پیش‌فرض
        self.main_content.setCurrentIndex(0)
    def change_theme(self):
        theme_name = self.theme_combo.currentText()
        if theme_name == "پیش‌فرض":
            self.setStyleSheet("")
        elif theme_name == "روشن":
            self.setStyleSheet("""
                QMainWindow { background-color: #f3f4f6; }
                QWidget { background-color: #ffffff; color: #1f2937; }
                QGroupBox { 
                    font-weight: bold; 
                    border: 1px solid #d1d5db; 
                    border-radius: 8px; 
                    margin-top: 10px; 
                    padding-top: 10px; 
                }
                QGroupBox::title { 
                    subcontrol-origin: margin; 
                    left: 10px; 
                    padding: 0 5px 0 5px; 
                }
                QPushButton { 
                    background-color: #3b82f6; 
                    color: white; 
                    border-radius: 8px; 
                    padding: 10px 15px; 
                    font-weight: bold; 
                }
                QPushButton:hover { background-color: #2563eb; }
                QPushButton:pressed { background-color: #1d4ed8; }
                QLineEdit, QComboBox, QSpinBox { 
                    padding: 8px; 
                    border: 1px solid #d1d5db; 
                    border-radius: 6px; 
                    background-color: white; 
                    color: #1f2937; 
                }
                QLineEdit:focus, QComboBox:focus, QSpinBox:focus { 
                    border: 2px solid #3b82f6; 
                }
                QTableWidget { 
                    gridline-color: #e5e7eb; 
                    background-color: white; 
                    alternate-background-color: #f9fafb; 
                }
                QHeaderView::section { 
                    background-color: #f3f4f6; 
                    padding: 8px; 
                    border: 1px solid #d1d5db; 
                    font-weight: bold; 
                }
            """)
        elif theme_name == "تاریک":
            self.setStyleSheet("""
                QMainWindow { background-color: #111827; }
                QWidget { background-color: #1f2937; color: #f9fafb; }
                QGroupBox { 
                    font-weight: bold; 
                    border: 1px solid #374151; 
                    border-radius: 8px; 
                    margin-top: 10px; 
                    padding-top: 10px; 
                }
                QGroupBox::title { 
                    subcontrol-origin: margin; 
                    left: 10px; 
                    padding: 0 5px 0 5px; 
                    color: #f9fafb; 
                }
                QPushButton { 
                    background-color: #1e40af; 
                    color: white; 
                    border-radius: 8px; 
                    padding: 10px 15px; 
                    font-weight: bold; 
                }
                QPushButton:hover { background-color: #1e3a8a; }
                QPushButton:pressed { background-color: #1e3a8a; }
                QLineEdit, QComboBox, QSpinBox { 
                    padding: 8px; 
                    border: 1px solid #374151; 
                    border-radius: 6px; 
                    background-color: #374151; 
                    color: #f9fafb; 
                }
                QLineEdit:focus, QComboBox:focus, QSpinBox:focus { 
                    border: 2px solid #3b82f6; 
                }
                QTableWidget { 
                    gridline-color: #374151; 
                    background-color: #374151; 
                    alternate-background-color: #4b5563; 
                }
                QHeaderView::section { 
                    background-color: #374151; 
                    padding: 8px; 
                    border: 1px solid #4b5563; 
                    font-weight: bold; 
                    color: #f9fafb; 
                }
            """)
        elif theme_name == "آبی":
            self.setStyleSheet("""
                QMainWindow { background-color: #eff6ff; }
                QWidget { background-color: #ffffff; color: #1e40af; }
                QPushButton { 
                    background-color: #1e40af; 
                    color: white; 
                    border-radius: 8px; 
                    padding: 10px 15px; 
                    font-weight: bold; 
                }
                QPushButton:hover { background-color: #1e3a8a; }
            """)
        elif theme_name == "قرمز":
            self.setStyleSheet("""
                QMainWindow { background-color: #fef2f2; }
                QWidget { background-color: #ffffff; color: #dc2626; }
                QPushButton { 
                    background-color: #dc2626; 
                    color: white; 
                    border-radius: 8px; 
                    padding: 10px 15px; 
                    font-weight: bold; 
                }
                QPushButton:hover { background-color: #b91c1c; }
            """)

    def apply_language(self):
        translations = {
            "fa": {
                "create_certificate": "ثبت گواهی جدید",
                "new_policy": "ثبت بیمه‌نامه جدید",
                "manage_companies": "مدیریت شرکت‌ها",
                "history": "سوابق اسناد",
                "reports": "گزارش مانده بیمه‌نامه‌ها",
                "backup": "پشتیبان‌گیری",
                "restore": "بازیابی",
                "register_certificate": "ثبت و چاپ گواهی"
            },
            "en": {
                "create_certificate": "Create New Certificate",
                "new_policy": "Create New Policy",
                "manage_companies": "Manage Companies",
                "history": "Certificate History",
                "reports": "Policy Balance Reports",
                "backup": "Backup",
                "restore": "Restore",
                "register_certificate": "Register and Print Certificate"
            }
        }
        
        lang_info = self.languages.get(self.current_language, self.languages["fa"])
        QApplication.instance().setLayoutDirection(lang_info["direction"])

    def setup_certificate_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form_layout = QFormLayout()
        
        self.company_combo_cert = QComboBox()
        self.company_combo_cert.currentTextChanged.connect(self.load_policies_for_certificate)
        form_layout.addRow("شرکت:", self.company_combo_cert)
        
        self.policy_combo = QComboBox()
        form_layout.addRow("بیمه‌نامه:", self.policy_combo)
        
        self.sanad_id_label = QLabel()
        form_layout.addRow("شماره سند:", self.sanad_id_label)
        
        self.sanad_date_edit = QLineEdit()
        self.sanad_date_edit.setText(self.get_persian_date())
        form_layout.addRow("تاریخ سند:", self.sanad_date_edit)
        
        self.cottage_edit = QLineEdit()
        form_layout.addRow("شماره کوتاژها:", self.cottage_edit)
        
        self.count_spin = QSpinBox()
        self.count_spin.setMaximum(9999)
        form_layout.addRow("تعداد:", self.count_spin)
        
        self.value_edit = QLineEdit()
        self.value_edit.textChanged.connect(self.format_currency)
        form_layout.addRow("ارزش (ریال):", self.value_edit)
        
        layout.addLayout(form_layout)
        
        self.register_button = QPushButton("ثبت و چاپ گواهی")
        self.register_button.clicked.connect(self.register_certificate)
        layout.addWidget(self.register_button)
        
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.warning_label)
        
        self.main_content.addTab(tab, "ثبت گواهی")

    def setup_policy_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form_layout = QFormLayout()
        
        self.company_combo_policy = QComboBox()
        self.company_combo_policy.currentTextChanged.connect(self.load_policies_for_policy_tab)
        form_layout.addRow("شرکت:", self.company_combo_policy)
        
        self.policy_number_edit = QLineEdit()
        form_layout.addRow("شماره بیمه‌نامه:", self.policy_number_edit)
        
        self.policy_date_edit = QLineEdit()
        self.policy_date_edit.setText(self.get_persian_date())
        form_layout.addRow("تاریخ بیمه‌نامه:", self.policy_date_edit)
        
        self.policy_value_edit = QLineEdit()
        self.policy_value_edit.textChanged.connect(self.format_currency)
        form_layout.addRow("ارزش کل بیمه‌نامه:", self.policy_value_edit)
        
        layout.addLayout(form_layout)
        
        save_policy_btn = QPushButton("ثبت بیمه‌نامه")
        save_policy_btn.clicked.connect(self.save_policy)
        layout.addWidget(save_policy_btn)
        
        self.policies_table = QTableWidget()
        self.policies_table.setColumnCount(6)
        self.policies_table.setHorizontalHeaderLabels(["شرکت", "شماره بیمه‌نامه", "تاریخ", "ارزش کل", "مانده", "درصد باقیمانده"])
        layout.addWidget(self.policies_table)
        
        self.main_content.addTab(tab, "بیمه‌نامه‌ها")

    def setup_companies_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        h_layout = QHBoxLayout()
        self.company_name_edit = QLineEdit()
        add_company_btn = QPushButton("افزودن شرکت")
        add_company_btn.clicked.connect(self.add_company)
        h_layout.addWidget(self.company_name_edit)
        h_layout.addWidget(add_company_btn)
        layout.addLayout(h_layout)
        
        self.companies_table = QTableWidget()
        layout.addWidget(self.companies_table)
        
        self.main_content.addTab(tab, "شرکت‌ها")

    def setup_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        company_filter_combo = QComboBox()
        company_filter_combo.currentTextChanged.connect(self.load_history)
        layout.addWidget(company_filter_combo)
        
        self.history_table = QTableWidget()
        layout.addWidget(self.history_table)
        
        self.main_content.addTab(tab, "سوابق")

    def setup_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form_layout = QFormLayout()
        self.report_company_combo = QComboBox()
        self.report_company_combo.currentTextChanged.connect(self.generate_report)
        form_layout.addRow("انتخاب شرکت:", self.report_company_combo)
        layout.addLayout(form_layout)
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)
        
        self.main_content.addTab(tab, "گزارش مانده")

    def change_language(self):
        lang_code = self.language_combo.currentData()
        self.current_language = lang_code
        self.apply_language()

    def apply_language(self):
        translations = {
            "fa": {
                "create_certificate": "ثبت گواهی جدید",
                "new_policy": "ثبت بیمه‌نامه جدید",
                "manage_companies": "مدیریت شرکت‌ها",
                "history": "سوابق اسناد",
                "reports": "گزارش مانده بیمه‌نامه‌ها",
                "backup": "پشتیبان‌گیری",
                "restore": "بازیابی",
                "register_certificate": "ثبت و چاپ گواهی",
                "duplicate_warning": "اخطار: این شماره‌های کوتاژ قبلاً در اسناد زیر استفاده شده‌اند:"
            },
            "en": {
                "create_certificate": "Create New Certificate",
                "new_policy": "Create New Policy",
                "manage_companies": "Manage Companies",
                "history": "Certificate History",
                "reports": "Policy Balance Reports",
                "backup": "Backup",
                "restore": "Restore",
                "register_certificate": "Register and Print Certificate",
                "duplicate_warning": "Warning: These cottage numbers have already been used in the following documents:"
            },
            "zh": {
                "create_certificate": "创建新保险证书",
                "new_policy": "创建新保险单",
                "manage_companies": "管理公司",
                "history": "证书记录",
                "reports": "保险单余额报告",
                "backup": "备份",
                "restore": "恢复",
                "register_certificate": "注册并打印证书",
                "duplicate_warning": "警告：这些货运号码已在以下文件中使用："
            },
            "ru": {
                "create_certificate": "Создать новое свидетельство",
                "new_policy": "Создать новую страховую полис",
                "manage_companies": "Управление компаниями",
                "history": "История документов",
                "reports": "Отчеты по остаткам страховых полисов",
                "backup": "Резервное копирование",
                "restore": "Восстановление",
                "register_certificate": "Зарегистрировать и распечатать свидетельство",
                "duplicate_warning": "Предупреждение: Эти номера коттеджей уже использовались в следующих документах:"
            }
        }
        
        lang_info = self.languages.get(self.current_language, self.languages["fa"])

    def format_currency(self, text):
        value = text.replace(",", "")
        try:
            num = int(value)
            formatted = "{:,}".format(num)
            if formatted != text:
                self.sender().setText(formatted)
        except ValueError:
            pass

    def get_persian_date(self):
        from jdatetime import datetime as jdatetime
        return jdatetime.now().strftime("%Y/%m/%d")

    def show_tab(self, index):
        self.main_content.setCurrentIndex(index)

    def load_companies(self, combo_box):
        """بارگذاری شرکت‌ها در یک ComboBox مشخص"""
        companies = self.db_manager.get_companies()
        if combo_box:
            combo_box.clear()
            combo_box.addItems([""] + companies)
    

    def refresh_all_company_combos(self):
        """بارگذاری شرکت‌ها در تمام ComboBox ها"""
        companies = self.db_manager.get_companies()
        combos_to_refresh = [
            self.company_combo_cert,
            self.company_combo_policy,
            self.report_company_combo
        ]
        
        for combo in combos_to_refresh:
            if combo is not None:
                combo.clear()
                combo.addItems([""] + companies)


    def load_policies_for_certificate(self):
        """بارگذاری بیمه‌نامه‌های مربوط به شرکت انتخاب شده"""
        company_name = self.company_combo_cert.currentText()
        self.policy_combo.clear()
        
        if not company_name or company_name == "":
            return
        
        policies = self.db_manager.get_policies(company_name)
        
        if not policies:
            self.policy_combo.addItem("هیچ بیمه‌نامه‌ای با مانده موجود نیست")
            return
        
        for policy in policies:
            policy_id, policy_number, policy_date, total_value, remaining_value = policy
            text = f"شماره {policy_number} - تاریخ {policy_date} - مانده: {remaining_value:,}"
            self.policy_combo.addItem(text, policy_id)
        
        if not policies:
            self.policy_combo.addItem("هیچ بیمه‌نامه‌ای یافت نشد")
            
    def register_certificate(self):
        cottage_numbers = self.cottage_edit.text().strip()
        if not cottage_numbers:
            QMessageBox.warning(self, "خطا", "شماره کوتاژها الزامی است")
            return

        existing_docs = self.db_manager.check_cottage_exists(cottage_numbers)
        if existing_docs:
            warning_msg = f"اخطار: این شماره‌های کوتاژ قبلاً در اسناد {', '.join(map(str, existing_docs))} استفاده شده‌اند"
            self.warning_label.setText(warning_msg)
        else:
            self.warning_label.setText("")

        try:
            value = int(self.value_edit.text().replace(",", ""))
        except ValueError:
            QMessageBox.warning(self, "خطا", "ارزش باید عدد معتبر باشد")
            return

        policy_index = self.policy_combo.currentIndex()
        if policy_index < 0:
            QMessageBox.warning(self, "خطا", "لطفاً بیمه‌نامه را انتخاب کنید")
            return

        policy_id = self.policy_combo.itemData(policy_index)
        company_name = self.company_combo_cert.currentText()
        sanad_id = self.db_manager.get_next_sanad_id()
        sanad_date = self.sanad_date_edit.text()

        success, remaining_after = self.db_manager.add_certificate(
            sanad_id, sanad_date, company_name, policy_id, 
            self.policy_combo.currentText().split(" - ")[0].replace("شماره ", ""),
            sanad_date, cottage_numbers, self.count_spin.value(), value
        )

        if success:
            certificate_data = {
                'sanad_id': sanad_id,
                'sanad_date': sanad_date,
                'company_name': company_name,
                'policy_number': self.policy_combo.currentText().split(" - ")[0].replace("شماره ", ""),
                'policy_date': sanad_date,
                'total_value': value,
                'cottage_numbers': cottage_numbers,
                'count': self.count_spin.value(),
                'value': value,
                'remaining_after': remaining_after
            }
            
            dialog = CertificatePrintDialog(certificate_data, self)
            dialog.exec()
            
            self.cottage_edit.clear()
            self.value_edit.clear()
            self.count_spin.setValue(1)
            self.load_policies_for_certificate()
            self.warning_label.setText("")
        else:
            QMessageBox.warning(self, "خطا", "موجودی بیمه‌نامه کافی نیست")

    def add_company(self):
        company_name = self.company_name_edit.text().strip()
        if not company_name:
            QMessageBox.warning(self, "خطا", "نام شرکت الزامی است")
            return
        
        if self.db_manager.add_company(company_name):
            QMessageBox.information(self, "موفق", "شرکت با موفقیت اضافه شد")
            self.company_name_edit.clear()
            self.refresh_all_company_combos()
            self.update_companies_table()
        else:
            QMessageBox.warning(self, "خطا", "این شرکت قبلاً ثبت شده است")

    def save_policy(self):
        company_name = self.company_combo_policy.currentText()
        policy_number = self.policy_number_edit.text().strip()
        policy_date = self.policy_date_edit.text().strip()
        
        try:
            policy_value = int(self.policy_value_edit.text().replace(",", ""))
        except ValueError:
            QMessageBox.warning(self, "خطا", "ارزش بیمه‌نامه باید عدد معتبر باشد")
            return

        if not all([company_name, policy_number, policy_date]):
            QMessageBox.warning(self, "خطا", "همه فیلدها الزامی هستند")
            return

        if self.db_manager.add_policy(company_name, policy_number, policy_date, policy_value):
            QMessageBox.information(self, "موفق", "بیمه‌نامه با موفقیت ثبت شد")
            self.policy_number_edit.clear()
            self.policy_value_edit.clear()
            self.update_policies_table()
        else:
            QMessageBox.warning(self, "خطا", "خطا در ثبت بیمه‌نامه")

    def update_companies_table(self):
        companies = self.db_manager.get_companies()
        self.companies_table.setRowCount(len(companies))
        self.companies_table.setColumnCount(1)
        self.companies_table.setHorizontalHeaderLabels(["نام شرکت"])
        
        for row, company in enumerate(companies):
            item = QTableWidgetItem(company)
            self.companies_table.setItem(row, 0, item)

    def load_policies_for_policy_tab(self):
        """بارگذاری لیست بیمه‌نامه‌ها در تب بیمه‌نامه‌ها"""
        company_name = self.company_combo_policy.currentText()
        self.update_policies_table(company_name)

    def update_policies_table(self, filter_company=None):
        
        policies = self.db_manager.get_policies(filter_company)
        self.policies_table.setRowCount(len(policies))
        
        for row, policy in enumerate(policies):
            company_name, policy_number, policy_date, total_value, remaining_value = policy[1], policy[2], policy[3], policy[4], policy[5]
            
            self.policies_table.setItem(row, 0, QTableWidgetItem(company_name))
            self.policies_table.setItem(row, 1, QTableWidgetItem(policy_number))
            self.policies_table.setItem(row, 2, QTableWidgetItem(policy_date))
            self.policies_table.setItem(row, 3, QTableWidgetItem(f"{total_value:,}"))
            self.policies_table.setItem(row, 4, QTableWidgetItem(f"{remaining_value:,}"))
            
            if total_value > 0:
                percentage = (remaining_value / total_value) * 100
                self.policies_table.setItem(row, 5, QTableWidgetItem(f"{percentage:.1f}%"))
            else:
                self.policies_table.setItem(row, 5, QTableWidgetItem("0%"))

    def backup_database(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "پشتیبان‌گیری", f"backup_{datetime.now().strftime('%Y%m%d')}.db", "Database Files (*.db)")
        if file_name:
            try:
                shutil.copy2("insurance_system.db", file_name)
                QMessageBox.information(self, "موفق", f"پشتیبان با موفقیت در فایل {file_name} ذخیره شد")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ایجاد پشتیبان: {str(e)}")

    def restore_database(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "بازیابی پشتیبان", "", "Database Files (*.db)")
        if file_name and QMessageBox.question(self, "تأیید", "آیا مطمئن هستید که می‌خواهید پایگاه داده را با فایل انتخاب شده جایگزین کنید؟") == QMessageBox.StandardButton.Yes:
            try:
                shutil.copy2(file_name, "insurance_system.db")
                QMessageBox.information(self, "موفق", "پایگاه داده با موفقیت بازیابی شد")
                self.load_companies()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در بازیابی پایگاه داده: {str(e)}")

    def load_history(self):
        # پیاده‌سازی نمایش سوابق
        pass

    def generate_report(self):
        company_name = self.report_company_combo.currentText()
        if not company_name:
            self.report_text.clear()
            return
        
        policies = self.db_manager.get_policies(company_name)
        report_text = f"گزارش مانده بیمه‌نامه‌های شرکت {company_name}:\n\n"
        
        for policy in policies:
            remaining_percent = (policy[4] / policy[3]) * 100 if policy[3] > 0 else 0
            report_text += f"شماره بیمه‌نامه: {policy[1]}\n"
            report_text += f"تاریخ: {policy[2]}\n"
            report_text += f"ارزش کل: {policy[3]:,} ریال\n"
            report_text += f"مانده: {policy[4]:,} ریال ({remaining_percent:.1f}%)\n"
            report_text += "-" * 40 + "\n"
        
        self.report_text.setPlainText(report_text)

def main():
    app = QApplication(sys.argv)
    
    # تنظیم فونت مناسب برای فارسی
    font = QFont("Tahoma", 9)
    app.setFont(font)
    
    window = InsuranceSystem()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()