// MIDI URL передається з шаблону result.html через {{ midi_file }}
const midiUrl = window.midiFile; // ми передамо змінну у шаблоні

// Ініціалізація MIDI Player
const player = new MidiPlayer.Player(function(event) {
  if (event.name === "Note on") {
    // Підсвічуємо клавішу
    const key = document.querySelector(`.key[data-note='${event.noteNumber}']`);
    if (key) key.classList.add('active');

    // Відтворення звуку через Tone.js
    const synth = new Tone.Synth().toDestination();
    synth.triggerAttackRelease(Tone.Frequency(event.noteNumber, "midi"), event.velocity/127);
  }
  if (event.name === "Note off") {
    const key = document.querySelector(`.key[data-note='${event.noteNumber}']`);
    if (key) key.classList.remove('active');
  }
});

// Завантаження MIDI файлу
fetch(midiUrl)
  .then(response => response.arrayBuffer())
  .then(data => player.loadArrayBuffer(data));

// Кнопка Play
document.getElementById('play').addEventListener('click', () => {
  Tone.start(); // Для браузерів на iOS/Chrome
  player.play();
});