from flask import Flask, request, render_template_string, send_file
import PyPDF2
import requests
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

last_summary = ""

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI PDF Summarizer</title>

<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
}

body{
    font-family:'Poppins',sans-serif;
    background:linear-gradient(135deg,#0f172a,#1e293b,#312e81);
    min-height:100vh;
    overflow-x:hidden;
    color:white;
}

.container{
    display:flex;
    min-height:100vh;
}

.left{
    width:40%;
    display:flex;
    justify-content:center;
    align-items:center;
    position:relative;
    overflow:hidden;
}

.left::before{
    content:'';
    position:absolute;
    width:500px;
    height:500px;
    background:rgba(255,255,255,0.08);
    border-radius:50%;
    top:-100px;
    left:-100px;
}

.left::after{
    content:'';
    position:absolute;
    width:300px;
    height:300px;
    background:rgba(255,255,255,0.05);
    border-radius:50%;
    bottom:-50px;
    right:-50px;
}

.logo-box{
    z-index:2;
    text-align:center;
}

.logo-box img{
    width:250px;
    filter:drop-shadow(0 10px 20px rgba(0,0,0,0.4));
    animation:float 3s ease-in-out infinite;
}

@keyframes float{
    0%{transform:translateY(0px);}
    50%{transform:translateY(-15px);}
    100%{transform:translateY(0px);}
}

.right{
    width:60%;
    display:flex;
    justify-content:center;
    align-items:center;
    padding:40px;
}

.card{
    width:100%;
    max-width:750px;
    background:rgba(255,255,255,0.12);
    backdrop-filter:blur(15px);
    border:1px solid rgba(255,255,255,0.2);
    border-radius:25px;
    padding:50px;
    box-shadow:0 10px 40px rgba(0,0,0,0.3);
}

h1{
    font-size:52px;
    font-weight:700;
    margin-bottom:10px;
}

.subtitle{
    color:#d1d5db;
    margin-bottom:35px;
    font-size:16px;
}

.upload-box{
    border:2px dashed rgba(255,255,255,0.4);
    border-radius:20px;
    padding:40px;
    text-align:center;
    transition:0.3s;
    background:rgba(255,255,255,0.05);
}

.upload-box:hover{
    background:rgba(255,255,255,0.1);
    transform:scale(1.01);
}

input[type=file]{
    color:white;
    font-size:15px;
}

.options{
    display:flex;
    gap:20px;
    margin-top:25px;
    flex-wrap:wrap;
}

.select-box{
    flex:1;
}

label{
    display:block;
    margin-bottom:8px;
    font-size:14px;
    color:#e5e7eb;
}

select{
    width:100%;
    padding:14px;
    border:none;
    border-radius:12px;
    background:white;
    font-size:15px;
    outline:none;
}

.btn{
    margin-top:30px;
    width:100%;
    padding:18px;
    border:none;
    border-radius:14px;
    background:linear-gradient(90deg,#4f46e5,#7c3aed);
    color:white;
    font-size:18px;
    font-weight:600;
    cursor:pointer;
    transition:0.3s;
    box-shadow:0 5px 20px rgba(79,70,229,0.5);
}

.btn:hover{
    transform:translateY(-2px);
    box-shadow:0 10px 25px rgba(79,70,229,0.7);
}

#spinner{
    display:none;
    margin:30px auto;
    border:6px solid rgba(255,255,255,0.2);
    border-top:6px solid white;
    border-radius:50%;
    width:55px;
    height:55px;
    animation:spin 1s linear infinite;
}

@keyframes spin{
    100%{
        transform:rotate(360deg);
    }
}

.result{
    margin-top:40px;
    background:white;
    color:#111827;
    padding:35px;
    border-radius:20px;
    line-height:1.8;
    box-shadow:0 10px 25px rgba(0,0,0,0.2);
    animation:fadeIn 0.7s ease;
}

@keyframes fadeIn{
    from{
        opacity:0;
        transform:translateY(20px);
    }
    to{
        opacity:1;
        transform:translateY(0);
    }
}

.result h3{
    margin-bottom:20px;
    color:#4f46e5;
    font-size:28px;
}

.download-btn{
    display:inline-block;
    margin-top:20px;
    padding:14px 28px;
    border-radius:12px;
    background:linear-gradient(90deg,#06b6d4,#2563eb);
    color:white;
    text-decoration:none;
    font-weight:600;
    transition:0.3s;
}

.download-btn:hover{
    transform:translateY(-2px);
}

.footer{
    margin-top:25px;
    text-align:center;
    color:#d1d5db;
    font-size:14px;
}

@media(max-width:900px){

.container{
    flex-direction:column;
}

.left{
    width:100%;
    height:250px;
}

.right{
    width:100%;
    padding:20px;
}

.card{
    padding:30px;
}

h1{
    font-size:38px;
}

}

</style>
</head>

<body>

<div class="container">

<div class="left">
<div class="logo-box">
<img src="https://cdn-icons-png.flaticon.com/512/337/337946.png">
<h2 style="margin-top:20px;">AI PDF Summarizer</h2>
</div>
</div>

<div class="right">

<div class="card">

<h1>Summarize PDFs Instantly</h1>
<p class="subtitle">
Upload your PDF and get AI-powered summaries in seconds.
</p>

<form id="form" method="POST" enctype="multipart/form-data">

<div class="upload-box">
<input type="file" name="pdf" required>
</div>

<div class="options">

<div class="select-box">
<label>Language</label>
<select name="language">
<option>English</option>
<option>Spanish</option>
<option>French</option>
<option>Arabic</option>
</select>
</div>

<div class="select-box">
<label>Summary Size</label>
<select name="size">
<option>Little</option>
<option>Medium</option>
<option>Full</option>
</select>
</div>

</div>

<button type="submit" class="btn" id="btn">
Generate Summary
</button>

</form>

<div id="spinner"></div>

{% if summary %}

<div class="result">
<h3>Summary Result</h3>
<p>{{summary}}</p>

<a href="/download" class="download-btn">
Download Summary PDF
</a>
</div>

{% endif %}

<div class="footer">
Powered by Flask + Ollama + Phi3
</div>

</div>

</div>
</div>

<script>

document.getElementById("form").addEventListener("submit", function(){

document.getElementById("btn").style.display = "none";
document.getElementById("spinner").style.display = "block";

});

</script>

</body>
</html>
"""

def extract_text(file, max_chars):

    reader = PyPDF2.PdfReader(file)
    text = ""

    for page in reader.pages:

        text += page.extract_text() or ""

        if len(text) >= max_chars:
            break

    return text[:max_chars]

def build_prompt(text, size, language):

    if size == "Little":

        instruction = "Summarize in 5 short bullet points."
        tokens = 120

    elif size == "Medium":

        instruction = """
Write a clear summary in 4 paragraphs.
Include the main ideas and conclusions.
"""
        tokens = 250

    else:

        instruction = """
Write a long and detailed summary.

Requirements:
- Add a title
- Use section headings
- Explain all major ideas
- Include important details and examples
- Write at least 8 paragraphs
- Be comprehensive
"""
        tokens = 700

    prompt = f"""
You are an expert PDF summarizer.

Respond only in {language}.

{instruction}

PDF Content:
{text}
"""

    return prompt, tokens

def llama_summary(prompt, tokens):

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": tokens,
                    "temperature": 0.2
                }
            },
            timeout=600
        )

        return response.json().get("response", "No response.")

    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():

    global last_summary

    summary = None

    if request.method == "POST":

        file = request.files["pdf"]
        size = request.form["size"]
        language = request.form["language"]

        if size == "Little":
            text = extract_text(file, 2500)

        elif size == "Medium":
            text = extract_text(file, 4000)

        else:
            text = extract_text(file, 7000)

        prompt, tokens = build_prompt(text, size, language)

        summary = llama_summary(prompt, tokens)

        last_summary = summary

    return render_template_string(HTML, summary=summary)

@app.route("/download")
def download_summary():

    global last_summary

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>PDF Summary</b>", styles['Title']))
    story.append(Spacer(1,20))

    story.append(Paragraph(last_summary.replace("\n","<br/>"), styles['BodyText']))

    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="summary.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(debug=True)