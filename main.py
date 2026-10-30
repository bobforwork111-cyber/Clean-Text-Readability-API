from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import re
import unicodedata

app = FastAPI(
    title="Clean Text & Readability API",
    description="Simple API to clean raw text, extract metrics, and measure readability scores.",
    version="1.0.0"
)

# Allow CORS for direct dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextPayload(BaseModel):
    text: str = Field(..., example="This is a simple sample text to clean and evaluate readability score.")


def clean_english_text(text: str) -> str:
    text = text.translate(str.maketrans({
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
    }))
    normalized_text = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(
        character if ord(character) < 128
        else " " if unicodedata.category(character).startswith(("L", "S", "P"))
        else ""
        for character in normalized_text
    )
    cleaned_text = re.sub(r"[^A-Za-z0-9\s.,!?'-]", " ", ascii_text)
    cleaned_text = re.sub(r"(?<![A-Za-z0-9])['-]+|['-]+(?![A-Za-z0-9])", " ", cleaned_text)
    cleaned_text = re.sub(r"\s+([,.!?])", r"\1", cleaned_text)
    cleaned_text = re.sub(r"([.!?]+)(?=\S)", r"\1 ", cleaned_text)
    return re.sub(r"\s+", " ", cleaned_text).strip()


def correct_english_text(text: str) -> str:
    contractions = {
        "arent": "aren't",
        "cant": "can't",
        "couldnt": "couldn't",
        "didnt": "didn't",
        "doesnt": "doesn't",
        "dont": "don't",
        "hadnt": "hadn't",
        "hasnt": "hasn't",
        "havent": "haven't",
        "im": "I'm",
        "isnt": "isn't",
        "ive": "I've",
        "mustnt": "mustn't",
        "shouldnt": "shouldn't",
        "thats": "that's",
        "theyll": "they'll",
        "theyre": "they're",
        "theyve": "they've",
        "wasnt": "wasn't",
        "werent": "weren't",
        "whats": "what's",
        "whos": "who's",
        "wont": "won't",
        "wouldnt": "wouldn't",
        "youll": "you'll",
        "youre": "you're",
        "youve": "you've",
    }

    def restore_contraction(match: re.Match[str]) -> str:
        original = match.group(0)
        corrected = contractions[original.lower()]
        if original.isupper():
            return corrected.upper()
        if original[0].isupper():
            return corrected[0].upper() + corrected[1:]
        return corrected

    text = re.sub(
        r"\b(?:" + "|".join(contractions) + r")\b",
        restore_contraction,
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bi\b", "I", text)
    return re.sub(
        r"(^|[.!?]\s+)([a-z])",
        lambda match: match.group(1) + match.group(2).upper(),
        text,
    )


@app.get("/", response_class=HTMLResponse)
def health_check():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clean Text & Readability</title>
  <style>
    :root { color-scheme: light; font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif; color: #172033; background: #f4f7fb; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; padding: 48px 20px; }
    main { max-width: 760px; margin: 0 auto; }
    h1 { margin: 0 0 8px; font-size: clamp(1.8rem, 5vw, 2.5rem); letter-spacing: -0.04em; }
    .intro { margin: 0 0 28px; color: #596579; line-height: 1.6; }
    .card { padding: 24px; border: 1px solid #e1e7f0; border-radius: 16px; background: #fff; box-shadow: 0 12px 32px #1f3a5f0d; }
    label { display: block; margin-bottom: 10px; font-weight: 650; }
    textarea { display: block; width: 100%; min-height: 190px; resize: vertical; padding: 14px; border: 1px solid #ccd5e2; border-radius: 10px; font: inherit; line-height: 1.55; }
    textarea:focus { outline: 3px solid #b9d5ff; border-color: #3478d4; }
    button { margin-top: 14px; padding: 11px 18px; border: 0; border-radius: 9px; background: #2463c5; color: #fff; font: inherit; font-weight: 650; cursor: pointer; }
    button:disabled { opacity: .65; cursor: wait; }
    .error { margin: 14px 0 0; color: #b42318; }
    [hidden] { display: none !important; }
    #results { margin-top: 22px; }
    h2 { margin: 0 0 12px; font-size: 1.15rem; }
    #cleaned-text { overflow-wrap: anywhere; padding: 14px; border-radius: 10px; background: #f4f7fb; line-height: 1.6; }
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 10px; margin: 16px 0 0; }
    .metric { padding: 13px; border: 1px solid #e1e7f0; border-radius: 10px; }
    .metric dt { color: #596579; font-size: .82rem; }
    .metric dd { margin: 5px 0 0; font-size: 1.25rem; font-weight: 700; }
    @media (max-width: 520px) { body { padding: 28px 14px; } .card { padding: 18px; } }
  </style>
</head>
<body>
  <main>
    <h1>Clean Text &amp; Readability</h1>
    <p class="intro">Paste English text to clean up formatting and apply a few common grammar corrections. This local tool does not rewrite sentences or understand context.</p>
    <section class="card" aria-labelledby="input-heading">
      <h2 id="input-heading">Your text</h2>
      <form id="clean-form">
        <label for="text-input">Enter English text</label>
        <textarea id="text-input" name="text" placeholder="Type or paste text here..." required></textarea>
        <button id="submit-button" type="submit">Correct and analyze</button>
        <p id="error-message" class="error" role="alert" hidden></p>
      </form>
      <section id="results" aria-live="polite" hidden>
        <h2>Corrected text</h2>
        <div id="cleaned-text"></div>
        <h2 style="margin-top: 20px">Metrics</h2>
        <dl class="metrics">
          <div class="metric"><dt>Characters</dt><dd id="character-count"></dd></div>
          <div class="metric"><dt>Words</dt><dd id="word-count"></dd></div>
          <div class="metric"><dt>Sentences</dt><dd id="sentence-count"></dd></div>
          <div class="metric"><dt>Average word length</dt><dd id="avg-word-length"></dd></div>
          <div class="metric"><dt>Average sentence length</dt><dd id="avg-sentence-length"></dd></div>
        </dl>
      </section>
    </section>
  </main>
  <script>
    const form = document.getElementById("clean-form");
    const button = document.getElementById("submit-button");
    const errorMessage = document.getElementById("error-message");
    const results = document.getElementById("results");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorMessage.hidden = true;
      results.hidden = true;
      button.disabled = true;
      button.textContent = "Analyzing...";

      try {
        const response = await fetch("/v1/clean", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: document.getElementById("text-input").value })
        });
        const body = await response.json();
        if (!response.ok) {
          throw new Error(body.detail || "Unable to process this text.");
        }

        const data = body.data;
        document.getElementById("cleaned-text").textContent = data.corrected_text;
        for (const [id, value] of Object.entries(data.metrics)) {
          const elementId = id.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase()).replace(/^./, letter => letter.toLowerCase());
          const target = document.getElementById(elementId.replace(/([A-Z])/g, "-$1").toLowerCase());
          if (target) target.textContent = value;
        }
        results.hidden = false;
      } catch (error) {
        errorMessage.textContent = error.message;
        errorMessage.hidden = false;
      } finally {
        button.disabled = false;
        button.textContent = "Correct and analyze";
      }
    });
  </script>
</body>
</html>"""


@app.get("/health")
def health_check():
    return {"status": "online", "message": "Clean Text API is running smoothly."}

@app.post("/v1/clean")
def clean_and_analyze(payload: TextPayload):
    raw_text = payload.text.strip()

    if not raw_text:
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")

    cleaned_text = clean_english_text(raw_text)
    corrected_text = correct_english_text(cleaned_text)
    words = re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", corrected_text)
    word_count = len(words)
    if not word_count:
        raise HTTPException(status_code=400, detail="Text must contain English letters or numbers.")

    character_count = len(corrected_text)
    sentence_endings = list(re.finditer(r"[.!?]+(?=\s|$)", corrected_text))
    sentence_count = len(sentence_endings)
    if not sentence_endings or corrected_text[sentence_endings[-1].end():].strip():
        sentence_count += 1

    avg_word_length = round(
        sum(len(re.sub(r"[^A-Za-z0-9]", "", word)) for word in words) / word_count,
        2,
    )
    avg_sentence_length = round(word_count / sentence_count, 2) if sentence_count else 0

    return {
        "success": True,
        "data": {
            "cleaned_text": cleaned_text,
            "corrected_text": corrected_text,
            "metrics": {
                "character_count": character_count,
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_word_length": avg_word_length,
                "avg_sentence_length": avg_sentence_length
            }
        }
    }