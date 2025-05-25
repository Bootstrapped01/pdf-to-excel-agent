from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import pdfplumber, pandas as pd, tempfile
import openai
import os

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    with pdfplumber.open(tmp_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"Extract a structured table from this construction scope document:\n{text}\nFields: item, quantity, unit."
        }]
    )

    structured_data = eval(response['choices'][0]['message']['content'])  # safer in final version
    df = pd.DataFrame(structured_data)

    output = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(output.name, index=False)

    return {"download_url": f"/download/{output.name.split('/')[-1]}"}

@app.get("/download/{filename}")
def download_excel(filename: str):
    file_path = f"/tmp/{filename}"
    return FileResponse(path=file_path, filename=filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
