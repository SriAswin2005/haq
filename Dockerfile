# Haq (AI lawyer) web app. Works on Hugging Face Spaces (Docker SDK), Render, Railway or any Docker host.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860
RUN useradd -m -u 1000 user
WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user . .
USER user
EXPOSE 7860
CMD ["sh", "-c", "python -m uvicorn app.server:app --host 0.0.0.0 --port ${PORT}"]
