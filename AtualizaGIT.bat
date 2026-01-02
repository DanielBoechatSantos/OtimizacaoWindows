@echo off
git add .

set /p texto="Digite a mensagem do commit: "

git commit -m "%texto%"

timeout /t 1
git push

echo.
echo Processo concluido com sucesso!
pause