"""Cria o database 'agenda' no MySQL, caso ainda não exista.

Uso:  python criar_banco.py
"""
import pymysql

from app.core.config import settings

conexao = pymysql.connect(
    host=settings.db_host or "localhost",
    port=settings.db_port,
    user=settings.db_user or "root",
    password=settings.db_password,
)
try:
    with conexao.cursor() as cursor:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conexao.commit()
    print(f"Database '{settings.db_name}' pronto.")
finally:
    conexao.close()
