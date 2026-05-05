# ── AWS Lambda Python 3.11 container image ────────────────────────────────────
FROM public.ecr.aws/lambda/python:3.11

# Patch OS packages from the base image (e.g. glibc CVE-2026-4046)
# and install system dependencies required by pytesseract (OCR)
# and pdfplumber (PDF rendering). Single RUN layer keeps the image small.
RUN yum update -y \
    && yum install -y \
        tesseract \
        tesseract-langdata-fra \
        tesseract-langdata-eng \
        poppler-utils \
    && yum clean all \
    && rm -rf /var/cache/yum

# Copy and install Python dependencies first (Docker layer cache)
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY agents/         ${LAMBDA_TASK_ROOT}/agents/
COPY email_gateway/  ${LAMBDA_TASK_ROOT}/email_gateway/
COPY utils/          ${LAMBDA_TASK_ROOT}/utils/
COPY db/             ${LAMBDA_TASK_ROOT}/db/
COPY prompts/        ${LAMBDA_TASK_ROOT}/prompts/
COPY config.py                  ${LAMBDA_TASK_ROOT}/
COPY logger.py                  ${LAMBDA_TASK_ROOT}/
COPY observability.py           ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py          ${LAMBDA_TASK_ROOT}/
COPY offer_collector_handler.py ${LAMBDA_TASK_ROOT}/

# Lambda entry point: file.function
CMD ["lambda_handler.handler"]
