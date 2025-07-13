import streamlit as st
import os
import tempfile
import re
import fitz  # PyMuPDF

st.set_page_config(
    page_title="Textbook Summary Generator",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'detected_subject' not in st.session_state:
    st.session_state.detected_subject = ""

def extract_text_from_pdf(pdf_file):
    try:
        pdf_bytes = pdf_file.read()
        if len(pdf_bytes) > 100 * 1024 * 1024:
            return "Error: PDF file is too large (>100MB)."

        temp_path = os.path.join(st.session_state.temp_dir, "temp.pdf")
        with open(temp_path, "wb") as f:
            f.write(pdf_bytes)

        doc = fitz.open(temp_path)

        text = ""
        for page in doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4].strip()
                if block_text:
                    text += block_text + "\n"

        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        text = text.replace('\xad', '')  # Remove soft hyphens
        text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)

        return text if text else "Could not extract meaningful text from PDF."
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def detect_subject(text):
    subjects_keywords = {
        "Computer Science": ["algorithm", "data structure", "programming", "computer", "network", "operating system", "machine learning", "database", "software", "hardware"],
        "Mathematics": ["theorem", "proof", "equation", "algebra", "calculus", "geometry", "function", "integral", "matrix"],
        "Physics": ["quantum", "force", "energy", "particle", "relativity", "mass", "velocity", "field", "wave"],
        "Chemistry": ["molecule", "atom", "reaction", "compound", "chemical", "bond", "acid", "base", "element"],
        "Biology": ["cell", "enzyme", "gene", "organism", "species", "dna", "evolution", "protein", "metabolism"],
        "Engineering": ["circuit", "signal", "control", "mechanical", "electrical", "design", "system", "process", "material"],
        "Economics": ["market", "demand", "supply", "inflation", "trade", "capital", "investment", "economy"],
        "Psychology": ["behavior", "cognition", "perception", "memory", "emotion", "therapy", "mental"],
        "Sociology": ["society", "culture", "social", "group", "institution", "inequality"],
        "History": ["empire", "war", "revolution", "dynasty", "colonial", "kingdom", "battle"],
        "Philosophy": ["ethics", "existence", "knowledge", "logic", "morality", "consciousness"],
        "Medicine": ["disease", "diagnosis", "treatment", "patient", "therapy", "symptom", "virus", "bacteria"],
        "Law": ["court", "law", "justice", "contract", "crime", "legal", "rights"],
        "Literature": ["novel", "poetry", "character", "theme", "narrative", "literary"],
        "Business": ["management", "marketing", "finance", "strategy", "organization", "leadership"],
    }

    lower_text = text.lower()
    subject_scores = {}
    for subject, keywords in subjects_keywords.items():
        count = 0
        for kw in keywords:
            count += lower_text.count(kw)
        subject_scores[subject] = count

    best_subject = max(subject_scores, key=subject_scores.get)
    if subject_scores[best_subject] == 0:
        return "General"
    return best_subject

def clean_extracted_text(raw_text, subject):
    lines = raw_text.split('\n')
    filtered_lines = []
    # Pattern to detect repeated author/book/version info lines to filter out
    skip_patterns = [
        r'silberschatz', r'galvin', r'gagne', r'©\d{4}', r'operating system concepts', 
        r'chapter \d+', r'edition', r'copyright', r'all rights reserved',
        r'published by', r'print', r'page \d+',
    ]
    skip_regex = re.compile('|'.join(skip_patterns), re.I)

    # Track lines to filter out duplicates (to remove repeated lines)
    seen = set()
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        # Skip lines that match any skip pattern
        if skip_regex.search(line_clean):
            continue
        # Skip lines that are very short and repetitive (like just numbers or single words)
        if len(line_clean) < 3 and line_clean.isdigit():
            continue
        # Skip duplicates
        if line_clean in seen:
            continue
        seen.add(line_clean)
        filtered_lines.append(line_clean)
    return '\n'.join(filtered_lines)

def normalize_bullets_and_lines(text):
    text = re.sub(r'[•♦\*\-]', '-', text)
    lines = text.split('\n')
    new_lines = []
    buffer = ""
    for line in lines:
        line = line.strip()
        if not line:
            if buffer:
                new_lines.append(buffer.strip())
                buffer = ""
            new_lines.append("")
            continue
        if line.startswith('-'):
            if buffer:
                new_lines.append(buffer.strip())
            buffer = line[1:].strip()
        else:
            if buffer:
                buffer += " " + line
            else:
                new_lines.append(line)
    if buffer:
        new_lines.append(buffer.strip())
    return '\n\n'.join(new_lines)

def create_technical_summary(text, subject, num_sentences=8):
    try:
        subject_keywords = {
            "computer science": r'\d+|[A-Z]{2,}|\b(?:algorithm|method|system|data|analysis|process|memory|program|device|execution|service|network|software|hardware)\b',
            "mathematics": r'\b(?:theorem|proof|equation|algebra|calculus|geometry|function|integral|matrix)\b',
            "physics": r'\b(?:quantum|force|energy|particle|relativity|mass|velocity|field|wave)\b',
            "chemistry": r'\b(?:molecule|atom|reaction|compound|chemical|bond|acid|base|element)\b',
            "biology": r'\b(?:cell|enzyme|gene|organism|species|dna|evolution|protein|metabolism)\b',
            "engineering": r'\b(?:circuit|signal|control|mechanical|electrical|design|system|process|material)\b',
            "economics": r'\b(?:market|demand|supply|inflation|trade|capital|investment|economy)\b',
            "psychology": r'\b(?:behavior|cognition|perception|memory|emotion|therapy|mental)\b',
            "sociology": r'\b(?:society|culture|social|group|institution|inequality)\b',
            "history": r'\b(?:empire|war|revolution|dynasty|colonial|kingdom|battle)\b',
            "philosophy": r'\b(?:ethics|existence|knowledge|logic|morality|consciousness)\b',
            "medicine": r'\b(?:disease|diagnosis|treatment|patient|therapy|symptom|virus|bacteria)\b',
            "law": r'\b(?:court|law|justice|contract|crime|legal|rights)\b',
            "literature": r'\b(?:novel|poetry|character|theme|narrative|literary)\b',
            "business": r'\b(?:management|marketing|finance|strategy|organization|leadership)\b',
            "general": r'\d+|[A-Z]{2,}|\b(?:concept|method|data|analysis|result|model|function)\b'
        }

        keywords_regex = subject_keywords.get(subject.lower(), subject_keywords["general"])

        headings = re.findall(r'^\s*(?:[\d.]+[.\s]+)?([A-Z][A-Z\s\-:]{2,}[A-Z])\s*$', text, re.MULTILINE)

        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        def score_sentence(sentence, index, total_sentences):
            score = 0
            if re.search(keywords_regex, sentence, re.I):
                score += 2
            score += min(len(sentence.split()) / 10, 2)
            if index < 2 or index >= total_sentences - 2:
                score += 1
            return score

        scored = [(i, s, score_sentence(s, i, len(sentences))) for i, s in enumerate(sentences)]
        top = sorted(scored, key=lambda x: x[2], reverse=True)[:num_sentences]
        top_sorted = sorted(top, key=lambda x: x[0])

        summary_parts = []
        if headings:
            summary_parts.append("Summary covers these main topics:")
            for h in headings[:5]:
                summary_parts.append(f"- {h}")
            summary_parts.append("")

        summary_parts.append("Summary:")
        for _, sentence, _ in top_sorted:
            summary_parts.append(f"- {sentence}")

        summary_text = '\n\n'.join(summary_parts)
        if len(summary_text) > 2000:
            summary_text = summary_text[:2000].rsplit('\n', 1)[0]

        return summary_text if summary_text else text[:1000]
    except Exception as e:
        st.error(f"Summary error: {str(e)}")
        return text[:1000]


def main():
    st.title("📚 Textbook Summary Generator")
    st.markdown("Upload a textbook PDF and get an automatic subject-detected summary.")

    pdf_file = st.file_uploader("Upload Textbook PDF", type=["pdf"])

    if pdf_file and not st.session_state.processing:
        if st.button("Generate Summary"):
            st.session_state.processing = True
            with st.spinner("Processing..."):
                text = extract_text_from_pdf(pdf_file)
                if text.startswith("Error") or "Could not extract" in text:
                    st.error(text)
                    st.session_state.processing = False
                    return

                detected_subject = detect_subject(text)
                st.session_state.detected_subject = detected_subject
                st.info(f"Detected subject: {detected_subject}")

                cleaned_text = clean_extracted_text(text, detected_subject)
                cleaned_text = normalize_bullets_and_lines(cleaned_text)

                st.session_state.summary = create_technical_summary(cleaned_text, detected_subject)

            st.session_state.processing = False

    if st.session_state.summary:
        st.markdown("### Generated Summary")
        st.text_area("", st.session_state.summary, height=300, disabled=True)

        st.download_button(
            label="Download Summary as TXT",
            data=st.session_state.summary,
            file_name="summary.txt",
            mime="text/plain"
        )


if __name__ == "__main__":
    main()
