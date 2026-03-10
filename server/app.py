import os
import pretty_midi
from flask import Flask, render_template, request, send_file
import subprocess
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Еталонна гамма До мажор обидва напрямки (3-4 октава)
C_MAJOR_BOTH_WAYS = [
    "C3","D3","E3","F3","G3","A3","B3","C4",
    "B3","A3","G3","F3","E3","D3","C3"
]


def remove_extension(file):
    return ".".join(file.split('.')[:-1])


def transcribe(audio_path):
    midi_path = os.path.join(
        OUTPUT_FOLDER,
        remove_extension(os.path.basename(audio_path)) + ".mid"
    )
    subprocess.run(["transkun", audio_path, midi_path])
    return midi_path


def parse_midi(midi_file):
    midi = pretty_midi.PrettyMIDI(midi_file)
    notes = []
    for instrument in midi.instruments:
        for note in instrument.notes:
            notes.append({
                "start": round(note.start,2),
                "end": round(note.end,2),
                "duration": round(note.end-note.start,2),
                "note": pretty_midi.note_number_to_name(note.pitch),
                "velocity": note.velocity
            })
    return notes


def plot_notes(notes):
    import pandas as pd
    df = pd.DataFrame(notes)

    fig = Figure(figsize=(12, 4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    sc = ax.scatter(df['start'], df['note'].apply(lambda x: pretty_midi.note_name_to_number(x)),
                    s=40, c=df['velocity'], cmap='viridis', alpha=0.7)
    ax.set_xlabel('Час (секунди)')
    ax.set_ylabel('MIDI pitch')
    ax.set_title('Piano-roll графік нот')
    fig.colorbar(sc, ax=ax, label='Velocity (гучність)')
    ax.grid(True)

    buf = io.BytesIO()
    fig.tight_layout()
    canvas.print_png(buf)
    data = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{data}"


def evaluate_midi(notes, correct_notes):
    user_notes = [n["note"] for n in notes]
    user_set = set(user_notes)
    correct_set = set(correct_notes)

    missing_notes = correct_set - user_set
    extra_notes = user_set - correct_set

    is_correct_set = missing_notes == set() and extra_notes == set()
    is_correct_sequence = user_notes == correct_notes

    return {
        "user_notes": user_notes,
        "missing_notes": list(missing_notes),
        "extra_notes": list(extra_notes),
        "is_correct_set": is_correct_set,
        "is_correct_sequence": is_correct_sequence
    }


@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        file = request.files["audio"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            midi_path = transcribe(filepath)
            notes = parse_midi(midi_path)
            plot_url = plot_notes(notes)
            evaluation = evaluate_midi(notes, C_MAJOR_BOTH_WAYS)

            return render_template(
                "result.html",
                notes=notes,
                midi_file=midi_path,
                plot_url=plot_url,
                evaluation=evaluation
            )

    return render_template("index.html")


@app.route("/download")
def download():
    return send_file(request.args.get("file"), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)