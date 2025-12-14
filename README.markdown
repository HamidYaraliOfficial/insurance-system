Insurance Certificate Management System
English
Overview
The Insurance Certificate Management System is a comprehensive desktop application designed for managing insurance policies and issuing cargo transport certificates. This professional software provides a complete solution for insurance agencies to register policies, issue certificates, track remaining policy values, and maintain detailed records of all transactions.
Key Features

Certificate Issuance: Register new certificates with automatic document numbering and policy balance deduction
Policy Management: Create and manage insurance policies with remaining value tracking
Company Management: Maintain a database of insurance client companies
Certificate Printing: Generate professional, formatted certificate documents with all required information
Balance Control: Automatic deduction of certificate values from policy remaining balances
Duplicate Detection: Warning system for detecting previously used cottage numbers
Data Management: Complete backup and restore functionality for database management
Reporting: Generate detailed reports showing remaining balances for each policy

System Components

Database Structure:Table NamePurposecompaniesInsurance client company recordspoliciesInsurance policy information with total and remaining valuescertificatesIssued certificates with associated policy and cottage number information
Primary Operations:OperationDescriptionCertificate RegistrationCreate new certificates with automatic policy balance reductionPolicy RegistrationCreate new insurance policies with specified total valueCottage Number CheckVerify cottage numbers have not been previously used

Requirements

Python 3.8 or higher
PyQt6

Installation

Install the required dependency:Bashpip install PyQt6
Run the application:Bashpython insurance_system.py

Usage
The application provides a tabbed interface with the following main functions:

Certificate Registration: Select company and policy, enter cottage numbers, quantity and value, then register and print the certificate
Policy Management: Create new insurance policies and monitor remaining balances
Company Management: Add and maintain insurance client companies
Certificate History: View previously issued certificates
Balance Reports: Generate reports showing remaining values for specific policies


فارسی
بررسی اجمالی
نرم‌افزار مدیریت صدور گواهی بیمه باربری یک برنامه جامع و حرفه‌ای برای مدیریت بیمه‌نامه‌ها و صدور گواهی‌های حمل بار است. این نرم‌افزار راه‌حلی کامل برای نمایندگی‌های بیمه فراهم می‌کند تا بتوانند بیمه‌نامه‌ها را ثبت کرده، گواهی‌های حمل صادر نمایند، مانده ارزش بیمه‌نامه‌ها را پیگیری کرده و سوابق کاملی از تمام عملیات را نگهداری کنند.
ویژگی‌های کلیدی

صدور گواهی: ثبت گواهی‌های جدید با شماره‌گذاری خودکار و کسر خودکار از مانده بیمه‌نامه
مدیریت بیمه‌نامه: ایجاد و مدیریت بیمه‌نامه‌ها با ردیابی مانده ارزش
مدیریت شرکت‌ها: نگهداری بانک اطلاعاتی شرکت‌های بیمه‌گذار
چاپ گواهی: تولید اسناد گواهی حرفه‌ای و فرمت‌بندی شده
کنترل مانده: کسر خودکار ارزش گواهی از مانده بیمه‌نامه مربوطه
تشخیص تکراری: سیستم هشدار برای تشخیص شماره‌های کوتاژ قبلاً استفاده شده
مدیریت داده‌ها: قابلیت پشتیبان‌گیری و بازیابی کامل پایگاه داده
گزارش‌گیری: تولید گزارش‌های تفصیلی از مانده بیمه‌نامه‌ها

اجزای سیستم

ساختار پایگاه داده:نام جدولکاربردcompaniesاطلاعات شرکت‌های بیمه‌گذارpoliciesاطلاعات بیمه‌نامه‌ها همراه با ارزش کل و ماندهcertificatesاطلاعات گواهی‌های صادر شده

نیازمندی‌ها

پایتون 3.8 یا بالاتر
PyQt6

نصب

نصب وابستگی مورد نیاز:Bashpip install PyQt6
اجرای برنامه:Bashpython insurance_system.py

نحوه استفاده
نرم‌افزار دارای رابط کاربری مبتنی بر تب با عملکردهای اصلی زیر است:

ثبت گواهی: انتخاب شرکت و بیمه‌نامه، وارد کردن شماره‌های کوتاژ، تعداد و ارزش، سپس ثبت و چاپ گواهی
مدیریت بیمه‌نامه: ایجاد بیمه‌نامه‌های جدید و نظارت بر مانده آن‌ها
مدیریت شرکت‌ها: افزودن و نگهداری اطلاعات شرکت‌های بیمه‌گذار
سوابق گواهی: مشاهده گواهی‌های قبلاً صادر شده
گزارش مانده: تولید گزارش‌های مربوط به مانده ارزش بیمه‌نامه‌ها


中文
概述
保险证书管理系统是一款全面的桌面应用程序，专门用于管理保险单并颁发货物运输证书。该专业软件为保险公司提供了一个完整的解决方案，可以注册保险单、颁发运输证书、跟踪保险单剩余价值以及维护所有交易的详细记录。
主要特性

证书颁发：使用自动文档编号注册新证书，并自动从保险单余额中扣除
保单管理：创建和管理保险单，并跟踪剩余价值
公司管理：维护保险客户公司的数据库
证书打印：生成包含所有必要信息的专业格式化证书文档
余额控制：自动从相关保险单的剩余余额中扣除证书价值
重复检测：检测已使用过的小屋编号的警告系统
数据管理：数据库的完整备份和恢复功能
报告生成：生成显示每份保险单剩余余额的详细报告

系统组件

数据库结构：表名用途companies保险公司客户记录policies保险单信息，包括总价值和剩余价值certificates已颁发的证书及其相关保单和小屋编号信息

系统要求

Python 3.8 或更高版本
PyQt6

安装

安装所需依赖：Bashpip install PyQt6
运行应用程序：Bashpython insurance_system.py

使用方法
应用程序提供基于选项卡的界面，主要功能包括：

证书注册：选择公司和保单，输入小屋编号、数量和价值，然后注册并打印证书
保单管理：创建新的保险单并监控剩余余额
公司管理：添加和维护保险公司客户
证书历史：查看之前颁发的证书
余额报告：生成显示特定保单剩余价值的报告