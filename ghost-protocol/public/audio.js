// Ghost Protocol: Neon Maze — WebAudio: procedural synthwave sequencer + SFX.
// Two SFX (dash, fragment) are generated Higgsfield samples from assets/;
// everything else is synthesized. Mix targets: SFX ≈ -10 dBFS, music ≈ -18 dBFS.

const SCALES = { minor: [0, 2, 3, 5, 7, 8, 10] };
// per-chapter root notes (semitones from A2) for musical variety
const CH_ROOTS = [0, -2, 3, -4, 5, 1, -5];

export class GameAudio {
  constructor() {
    this.ctx = null;
    this.samples = {};
    this.mode = "off";
    this.chapter = 0;
    this.intensity = 0;
    this.musicVol = 0.7;
    this.sfxVol = 0.8;
    this._step = 0;
    this._nextTime = 0;
    this._timer = null;
  }

  init() {
    if (this.ctx) { if (this.ctx.state === "suspended") this.ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.7; // headroom: true-peak stays below -3 dBFS
    this.comp = this.ctx.createDynamicsCompressor();
    this.comp.threshold.value = -12;
    this.comp.ratio.value = 6;
    this.master.connect(this.comp);
    this.comp.connect(this.ctx.destination);
    this.musicGain = this.ctx.createGain();
    this.musicGain.gain.value = 0.13 * this.musicVol; // ≈ -18 dBFS under sfx
    this.musicGain.connect(this.master);
    this.sfxGain = this.ctx.createGain();
    this.sfxGain.gain.value = 0.32 * this.sfxVol;
    this.sfxGain.connect(this.master);
    this._loadSamples();
    this._timer = setInterval(() => this._schedule(), 40);
    this._nextTime = this.ctx.currentTime + 0.1;
  }

  setVolumes(music, sfx) {
    this.musicVol = music; this.sfxVol = sfx;
    if (this.ctx) {
      this.musicGain.gain.value = 0.13 * music;
      this.sfxGain.gain.value = 0.32 * sfx;
    }
  }

  async _loadSamples() {
    // generated Higgsfield SFX per assets/manifest.json (urls may be local or CDN);
    // any failure falls back to the built-in synthesizer.
    for (const [name, url] of Object.entries(this.sfxUrls || {})) {
      try {
        const res = await fetch(url);
        if (!res.ok) continue;
        const buf = await res.arrayBuffer();
        this.samples[name] = await this.ctx.decodeAudioData(buf);
      } catch { /* synth fallback covers it */ }
    }
  }

  setMode(mode, chapter = this.chapter) {
    this.mode = mode;
    this.chapter = chapter;
  }
  setIntensity(v) { this.intensity = Math.max(0, Math.min(1, v)); }

  // ---- sequencer ----
  _schedule() {
    if (!this.ctx || this.mode === "off") return;
    const bpm = this.mode === "boss" ? 148 : this.mode === "menu" ? 96 : this.mode === "ending" ? 76 : 112;
    const spb = 60 / bpm / 4; // 16th
    while (this._nextTime < this.ctx.currentTime + 0.15) {
      this._playStep(this._step, this._nextTime, spb);
      this._nextTime += spb;
      this._step = (this._step + 1) % 64;
    }
  }

  _note(semi) { return 110 * Math.pow(2, semi / 12); }

  _playStep(step, t, spb) {
    const ctx = this.ctx, root = CH_ROOTS[this.chapter] || 0;
    const scale = SCALES.minor;
    const boss = this.mode === "boss";
    const ending = this.mode === "ending";
    const bar = Math.floor(step / 16) % 4;
    const chordDeg = boss ? [0, 5, 3, 4][bar] : [0, 3, 4, 5][bar];
    const chordRoot = root + scale[chordDeg % 7] - 12;

    // kick on quarters (skip in ending mode)
    if (!ending && step % 4 === 0) this._kick(t, boss ? 1 : 0.8);
    // snare-ish noise on 2 & 4 in boss mode
    if (boss && step % 8 === 4) this._noiseHit(t, 900, 0.1, 0.5);
    // hats — density scales with intensity
    const hatEvery = this.intensity > 0.6 ? 1 : this.intensity > 0.25 ? 2 : 4;
    if (!ending && step % hatEvery === 0) this._noiseHit(t, 6000, 0.03, 0.16 + this.intensity * 0.12);
    // bass: driving 8ths
    if (step % 2 === 0) {
      const off = boss && step % 8 === 6 ? 3 : 0;
      this._bass(t, this._note(chordRoot + off), spb * (boss ? 1.6 : 1.9));
    }
    // arp: 16ths pattern
    const arpPat = [0, 2, 4, 2, 0, 4, 2, 4];
    if ((boss || this.intensity > 0.15 || this.mode === "menu" || ending) && step % (ending ? 4 : 2) === 1) {
      const deg = arpPat[(step >> 1) % 8];
      const oct = this.intensity > 0.5 && step % 8 > 4 ? 24 : 12;
      this._pluck(t, this._note(chordRoot + scale[deg % 7] + oct), spb * 1.5, ending ? 0.10 : 0.14);
    }
    // pad at bar starts
    if (step % 16 === 0) {
      this._pad(t, [chordRoot, chordRoot + scale[2], chordRoot + scale[4]].map(s => this._note(s + 12)), spb * 16);
    }
  }

  _env(g, t, a, d, peak) {
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(peak, t + a);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + d);
  }

  _kick(t, vel) {
    const ctx = this.ctx;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.frequency.setValueAtTime(130, t);
    o.frequency.exponentialRampToValueAtTime(38, t + 0.12);
    this._env(g, t, 0.002, 0.16, 0.9 * vel);
    o.connect(g); g.connect(this.musicGain);
    o.start(t); o.stop(t + 0.2);
  }

  _noiseHit(t, freq, dur, vel) {
    const ctx = this.ctx;
    const len = Math.max(1, Math.floor(ctx.sampleRate * dur));
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource(); src.buffer = buf;
    const f = ctx.createBiquadFilter(); f.type = "highpass"; f.frequency.value = freq;
    const g = ctx.createGain();
    this._env(g, t, 0.001, dur, vel * 0.5);
    src.connect(f); f.connect(g); g.connect(this.musicGain);
    src.start(t); src.stop(t + dur + 0.05);
  }

  _bass(t, freq, dur) {
    const ctx = this.ctx;
    const o = ctx.createOscillator(); o.type = "sawtooth"; o.frequency.value = freq;
    const f = ctx.createBiquadFilter(); f.type = "lowpass";
    f.frequency.setValueAtTime(900, t);
    f.frequency.exponentialRampToValueAtTime(180, t + dur);
    f.Q.value = 6;
    const g = ctx.createGain();
    this._env(g, t, 0.004, dur, 0.5);
    o.connect(f); f.connect(g); g.connect(this.musicGain);
    o.start(t); o.stop(t + dur + 0.05);
  }

  _pluck(t, freq, dur, vel) {
    const ctx = this.ctx;
    const o = ctx.createOscillator(); o.type = "square"; o.frequency.value = freq;
    const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.value = 2400;
    const g = ctx.createGain();
    this._env(g, t, 0.002, dur, vel);
    o.connect(f); f.connect(g); g.connect(this.musicGain);
    o.start(t); o.stop(t + dur + 0.05);
  }

  _pad(t, freqs, dur) {
    const ctx = this.ctx;
    for (const fr of freqs) {
      for (const det of [-6, 6]) {
        const o = ctx.createOscillator(); o.type = "sawtooth";
        o.frequency.value = fr; o.detune.value = det;
        const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.value = 700;
        const g = ctx.createGain();
        g.gain.setValueAtTime(0.0001, t);
        g.gain.linearRampToValueAtTime(0.05, t + dur * 0.3);
        g.gain.linearRampToValueAtTime(0.0001, t + dur);
        o.connect(f); f.connect(g); g.connect(this.musicGain);
        o.start(t); o.stop(t + dur + 0.1);
      }
    }
  }

  // ---- SFX ----
  playSfx(name, { pan = 0, vol = 1 } = {}) {
    if (!this.ctx) return;
    const ctx = this.ctx, t = ctx.currentTime;
    const out = ctx.createGain(); out.gain.value = vol;
    let p = out;
    if (ctx.createStereoPanner) {
      const pn = ctx.createStereoPanner(); pn.pan.value = Math.max(-1, Math.min(1, pan));
      out.connect(pn); pn.connect(this.sfxGain); p = out;
    } else out.connect(this.sfxGain);

    const sample = { dash: "sfx_dash", frag: "sfx_frag" }[name];
    if (sample && this.samples[sample]) {
      const src = ctx.createBufferSource();
      src.buffer = this.samples[sample];
      src.connect(p); src.start(t);
      return;
    }
    const osc = (type, f0, f1, dur, peak, curve = "exp") => {
      const o = ctx.createOscillator(); o.type = type;
      o.frequency.setValueAtTime(f0, t);
      if (f1) {
        if (curve === "exp") o.frequency.exponentialRampToValueAtTime(Math.max(1, f1), t + dur);
        else o.frequency.linearRampToValueAtTime(f1, t + dur);
      }
      const g = ctx.createGain();
      this._env(g, t, 0.003, dur, peak);
      o.connect(g); g.connect(p);
      o.start(t); o.stop(t + dur + 0.05);
    };
    const noise = (freq, dur, peak, type = "highpass") => {
      const len = Math.max(1, Math.floor(ctx.sampleRate * dur));
      const buf = ctx.createBuffer(1, len, ctx.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      const src = ctx.createBufferSource(); src.buffer = buf;
      const f = ctx.createBiquadFilter(); f.type = type; f.frequency.value = freq;
      const g = ctx.createGain();
      this._env(g, t, 0.002, dur, peak);
      src.connect(f); f.connect(g); g.connect(p);
      src.start(t); src.stop(t + dur + 0.05);
    };
    switch (name) {
      case "dash": noise(2000, 0.18, 0.5); osc("sine", 500, 900, 0.15, 0.2); break;
      case "frag": osc("sine", 880, 1760, 0.18, 0.4); osc("sine", 1320, 2640, 0.25, 0.25); break;
      case "shot": osc("square", 620, 180, 0.12, 0.3); break;
      case "eshot": osc("sawtooth", 300, 120, 0.16, 0.25); break;
      case "hit": noise(400, 0.12, 0.5, "lowpass"); osc("square", 160, 60, 0.12, 0.4); break;
      case "hurt": osc("sawtooth", 220, 70, 0.25, 0.5); noise(300, 0.2, 0.3, "lowpass"); break;
      case "emp": osc("sine", 60, 200, 0.5, 0.6, "lin"); noise(1200, 0.4, 0.5); break;
      case "alert": osc("square", 700, 1400, 0.12, 0.35); osc("square", 1400, 700, 0.12, 0.3); break;
      case "door": osc("sine", 200, 420, 0.25, 0.35); break;
      case "portal": osc("sine", 300, 1200, 0.4, 0.35); osc("sine", 450, 1800, 0.4, 0.2); break;
      case "save": osc("sine", 660, 990, 0.15, 0.3); osc("sine", 990, 1320, 0.25, 0.25); break;
      case "ui": osc("square", 900, 1100, 0.05, 0.18); break;
      case "uiback": osc("square", 600, 400, 0.06, 0.18); break;
      case "hack_ok": osc("sine", 520, 1040, 0.12, 0.3); osc("sine", 780, 1560, 0.2, 0.25); break;
      case "hack_fail": osc("sawtooth", 300, 90, 0.4, 0.4); break;
      case "boom": noise(200, 0.5, 0.8, "lowpass"); osc("sine", 120, 30, 0.5, 0.6); break;
      case "levelup": [523, 659, 784, 1046].forEach((f, i) => setTimeout(() => this.playSfx("_tone", { pan, vol: 0.6 - i * 0.08, _f: f }), i * 80)); break;
      case "_tone": osc("sine", arguments[1]?._f || 880, null, 0.18, 0.3); break;
      case "pickup": osc("sine", 700, 1000, 0.1, 0.3); break;
      case "mine": noise(500, 0.3, 0.6, "lowpass"); osc("square", 200, 50, 0.25, 0.5); break;
      case "teleport": osc("sine", 1400, 200, 0.25, 0.35); noise(3000, 0.15, 0.2); break;
      case "shield": osc("sine", 330, 660, 0.3, 0.3, "lin"); break;
      case "cloak": osc("sine", 800, 200, 0.35, 0.25); break;
      case "slow": osc("sine", 440, 110, 0.5, 0.3); break;
      case "invert": osc("sawtooth", 100, 800, 0.5, 0.35, "lin"); break;
      case "bossdie": noise(150, 1.2, 0.8, "lowpass"); osc("sine", 200, 25, 1.2, 0.6); break;
      case "achieve": osc("sine", 784, 1568, 0.3, 0.35); osc("sine", 1046, 2093, 0.4, 0.25); break;
      default: osc("sine", 440, null, 0.1, 0.2);
    }
  }
}
