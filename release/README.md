# Сборка для Linux

Готовый файл: `release/abramyan-exam-linux-x86_64` (после запуска
`scripts/build_linux.sh`). Это один self-contained ELF-бинарник для x86_64
Linux; Python и права администратора на целевой машине не нужны.

```bash
chmod +x abramyan-exam-linux-x86_64
./abramyan-exam-linux-x86_64
```

По умолчанию приложение откроет браузер на `http://127.0.0.1:8000/`, создаст
каталог `exam-data` рядом с исполняемым файлом и выведет в консоль ссылку на
панель преподавателя с токеном.

Для запуска в компьютерном классе:

```bash
EXAM_HOST=0.0.0.0 EXAM_OPEN_BROWSER=0 ./abramyan-exam-linux-x86_64
```

Подробности — в корневом `README.md`. SHA-256 сборки записывается в
`SHA256SUMS` при сборке.
