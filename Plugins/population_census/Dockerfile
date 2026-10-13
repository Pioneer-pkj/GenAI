FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full package (needed for relative imports)
COPY . ./population_census/

# Expose port (Cloud Run uses PORT env var, default 8080)
EXPOSE 8080

# Run Streamlit on Cloud Run's PORT
CMD streamlit run population_census/chatbot_ui.py \
    --server.port=${PORT:-8080} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
