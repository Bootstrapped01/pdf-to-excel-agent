from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import pdfplumber, pandas as pd, tempfile
import openai
import os
import json

app = FastAPI()
openai.api_key = os.getenv("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")

@app.post("/process-pdf/")
async def process_pdf(
    file: UploadFile = File(...),
    scope: str = Form(...)
):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    with pdfplumber.open(tmp_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": (
                    f"You are a construction estimator. Use the following scope of work to extract relevant structured data.\n"
                    f"SCOPE: {scope}\n"
                    f"DOCUMENT TEXT:\n{text}\n"
                    "Return a JSON array in the format: [{\"item\": \"Concrete Curb\", \"quantity\": 100, \"unit\": \"LF\"}, ...]"
                )
            }]
        )
    except Exception as e:
        return {"error": f"OpenAI API request failed: {e}"}

    try:
        structured_data = json.loads(response['choices'][0]['message']['content'])
    except Exception as e:
        return {
            "error": f"Failed to parse GPT response: {e}",
            "raw": response['choices'][0]['message']['content']
        }

    df = pd.DataFrame(structured_data)

    output = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(output.name, index=False)

    return {"download_url": f"/download/{output.name.split('/')[-1]}"}

@app.get("/download/{filename}")
def download_excel(filename: str):
    file_path = f"/tmp/{filename}"
    return FileResponse(path=file_path, filename=filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
