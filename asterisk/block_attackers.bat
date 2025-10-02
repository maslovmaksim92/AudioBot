@echo off
echo ========================================
echo Блокировка атакующих IP
echo ========================================
echo.

ssh -i C:\sshkeys\yc_ru_2025 ubuntu@51.250.74.43 -t "sudo ufw deny from 37.49.225.223 && sudo ufw deny from 198.23.190.62 && echo 'Атакующие IP заблокированы!' && sleep 3"

pause