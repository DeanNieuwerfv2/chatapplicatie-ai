# 1. Basis image: slanke Python 3.12
FROM python:3.12-slim

# 2. Pip up-to-date maken (optioneel maar handig)
RUN pip install --upgrade pip

# 3. Werkdirectory binnen de container
WORKDIR /app

# 4. Alleen requirements kopiëren (betere caching)
COPY requirements.txt .

# 5. Dependencies installeren
RUN pip install -r requirements.txt

# 6. De rest van de code kopiëren
COPY . .

# 7. Poort 8000 openzetten (hier draait uvicorn op)
EXPOSE 8000

# 8. Command om de FastAPI-app te starten
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
