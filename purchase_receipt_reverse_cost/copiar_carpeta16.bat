@echo off

set "ORIGEN=C:\Users\Dell\Documents\Modulos odoo 16\purchase_receipt_reverse_cost\purchase_receipt_reverse_cost"
set "DESTINO=C:\odoo16-test\addons\purchase_receipt_reverse_cost"

echo ========================================
echo Sincronizando modulo Odoo...
echo ========================================

robocopy "%ORIGEN%" "%DESTINO%" /MIR /COPY:DAT /R:2 /W:2

echo.
echo ========================================
echo Sincronizacion finalizada.
echo ========================================

echo.
echo Reiniciando Odoo...

cd /d "C:\odoo16-test"

docker compose restart 

echo.
echo ========================================
echo Odoo reiniciado.
echo ========================================

pause