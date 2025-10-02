@echo off
echo ========================================
echo Мониторинг Asterisk (БЕЗ СПАМА)
echo ========================================
echo Фильтруются атакующие IP
echo Показываются только реальные звонки
echo ========================================
echo.

ssh -i C:\sshkeys\yc_ru_2025 ubuntu@51.250.74.43 -t "sudo tail -f /var/log/asterisk/full | grep -v '37.49.225.223' | grep -v '198.23.190.62' | grep -E 'INVITE|livekit|161.115|35.'"

pause